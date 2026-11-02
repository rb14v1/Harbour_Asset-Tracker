from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assets.models import Asset, AssetAssignment
from apps.employees.models import Employee


class AssetAssignmentFlowTests(APITestCase):
    """Covers: double-assignment prevention, status derivation precedence,
    and the return-then-reassign flow."""

    def setUp(self):
        self.user = User.objects.create_user(email="hr2@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)
        self.asset = Asset.objects.create(asset_tag="T-0001", name="Test Laptop", category=Asset.Category.LAPTOP)
        self.alice = Employee.objects.create(name="Alice", email="alice@example.com")
        self.bob = Employee.objects.create(name="Bob", email="bob@example.com")

    def _assign(self, asset_id, employee_id, **extra):
        return self.client.post(reverse("asset-assign", args=[asset_id]), {"employee_id": employee_id, **extra})

    def test_assigning_available_asset_succeeds(self):
        response = self._assign(self.asset.id, self.alice.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Filtered to this test's own asset - the seed migration's demo
        # data is also present in the test DB (migrations run against it
        # too), so a global AssetAssignment.objects.count() would be
        # contaminated by that unrelated data.
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset).count(), 1)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)

    def test_double_assignment_is_rejected(self):
        first = self._assign(self.asset.id, self.alice.id)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self._assign(self.asset.id, self.bob.id)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            AssetAssignment.objects.filter(asset=self.asset).count(), 1,
            "must not silently create a second open assignment",
        )

    def test_double_assignment_rejected_at_db_level_too(self):
        """The partial unique constraint is the ultimate backstop even if
        application-level logic were bypassed (e.g. direct ORM usage)."""
        AssetAssignment.objects.create(asset=self.asset, employee=self.alice, assigned_date=date.today())
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            AssetAssignment.objects.create(asset=self.asset, employee=self.bob, assigned_date=date.today())

    def test_cannot_assign_retired_asset(self):
        self.asset.is_retired = True
        self.asset.save(update_fields=["is_retired"])
        response = self._assign(self.asset.id, self.alice.id)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset).count(), 0)

    def test_status_precedence_retired_overrides_open_assignment(self):
        """A retired asset reports status=retired even with an open
        assignment still on record (e.g. it was pulled from service without
        a formal return)."""
        AssetAssignment.objects.create(asset=self.asset, employee=self.alice, assigned_date=date.today())
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)

        retire_response = self.client.post(reverse("asset-retire", args=[self.asset.id]))
        self.assertEqual(retire_response.status_code, status.HTTP_200_OK)

        self.asset.refresh_from_db()
        self.assertTrue(self.asset.is_retired)
        self.assertEqual(self.asset.status, Asset.Status.RETIRED, "retired must win even over an open assignment")

        unretire_response = self.client.post(reverse("asset-unretire", args=[self.asset.id]))
        self.assertEqual(unretire_response.status_code, status.HTTP_200_OK)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED, "unretiring reveals the still-open assignment")

    def test_status_available_when_no_assignment_and_not_retired(self):
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)

    def test_return_then_reassign_flow(self):
        assign_response = self._assign(self.asset.id, self.alice.id)
        assignment_id = assign_response.data["id"]

        # Can't reassign while still open.
        blocked = self._assign(self.asset.id, self.bob.id)
        self.assertEqual(blocked.status_code, status.HTTP_409_CONFLICT)

        return_response = self.client.post(reverse("assignment-return", args=[assignment_id]))
        self.assertEqual(return_response.status_code, status.HTTP_200_OK)
        self.assertEqual(return_response.data["returned_date"], date.today().isoformat())

        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.AVAILABLE)

        reassign_response = self._assign(self.asset.id, self.bob.id)
        self.assertEqual(reassign_response.status_code, status.HTTP_201_CREATED)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.status, Asset.Status.ASSIGNED)
        self.assertEqual(AssetAssignment.objects.filter(asset=self.asset).count(), 2)

    def test_returning_already_returned_assignment_is_rejected(self):
        assign_response = self._assign(self.asset.id, self.alice.id)
        assignment_id = assign_response.data["id"]
        first_return = self.client.post(reverse("assignment-return", args=[assignment_id]))
        self.assertEqual(first_return.status_code, status.HTTP_200_OK)

        second_return = self.client.post(reverse("assignment-return", args=[assignment_id]))
        self.assertEqual(second_return.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_date_before_assigned_date_rejected(self):
        assign_response = self._assign(
            self.asset.id, self.alice.id, assigned_date=date.today().isoformat()
        )
        assignment_id = assign_response.data["id"]
        bad_date = (date.today() - timedelta(days=5)).isoformat()
        response = self.client.post(reverse("assignment-return", args=[assignment_id]), {"returned_date": bad_date})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_assignments_filterable_by_open(self):
        # Scoped by employee (not just `open`) since the seed migration's
        # demo data also has several open and returned assignments in the
        # same test DB.
        assign_response = self._assign(self.asset.id, self.alice.id)
        assignment_id = assign_response.data["id"]
        self.client.post(reverse("assignment-return", args=[assignment_id]))

        other_asset = Asset.objects.create(asset_tag="T-0002", name="Other Laptop", category=Asset.Category.LAPTOP)
        self._assign(other_asset.id, self.bob.id)

        open_only = self.client.get(reverse("assignment-list"), {"open": "true", "employee": self.bob.id})
        self.assertEqual(open_only.data["count"], 1)

        closed_only = self.client.get(reverse("assignment-list"), {"open": "false", "employee": self.alice.id})
        self.assertEqual(closed_only.data["count"], 1)

    def test_assignments_filterable_by_asset_and_employee(self):
        self._assign(self.asset.id, self.alice.id)
        by_asset = self.client.get(reverse("assignment-list"), {"asset": self.asset.id})
        self.assertEqual(by_asset.data["count"], 1)

        by_employee = self.client.get(reverse("assignment-list"), {"employee": self.alice.id})
        self.assertEqual(by_employee.data["count"], 1)

    def test_delete_asset_with_history_is_protected(self):
        self._assign(self.asset.id, self.alice.id)
        response = self.client.delete(reverse("asset-detail", args=[self.asset.id]))
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Asset.objects.filter(id=self.asset.id).exists())
