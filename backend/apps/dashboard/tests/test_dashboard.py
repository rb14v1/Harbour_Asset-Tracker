from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assets.models import Asset, AssetAssignment
from apps.employees.models import Employee


class DashboardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="hr3@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)

        # The seed migration's demo data is also present in the test DB (it
        # runs as part of building it), so dashboard counts are asserted as
        # deltas against this pre-fixture baseline rather than absolute
        # totals.
        self.baseline = self.client.get(reverse("dashboard")).data

        self.alice = Employee.objects.create(name="Alice", email="alice2@example.com")
        self.bob = Employee.objects.create(name="Bob", email="bob2@example.com")

        self.laptop_assigned = Asset.objects.create(
            asset_tag="D-0001", name="Laptop Assigned", category=Asset.Category.LAPTOP
        )
        self.laptop_retired = Asset.objects.create(
            asset_tag="D-0002", name="Laptop Retired", category=Asset.Category.LAPTOP, is_retired=True
        )
        self.monitor_available = Asset.objects.create(
            asset_tag="D-0003", name="Monitor Available", category=Asset.Category.MONITOR
        )
        self.phone_never_assigned = Asset.objects.create(
            asset_tag="D-0004", name="Phone Never Assigned", category=Asset.Category.PHONE
        )

        AssetAssignment.objects.create(asset=self.laptop_assigned, employee=self.alice, assigned_date=date.today())
        # Retired asset also has an open assignment on record - should still
        # count as "retired", not "assigned", and should still show up for
        # Bob's currently-assigned list (physical custody tracking).
        AssetAssignment.objects.create(asset=self.laptop_retired, employee=self.bob, assigned_date=date.today())
        AssetAssignment.objects.create(
            asset=self.monitor_available, employee=self.bob, assigned_date=date.today(), returned_date=date.today()
        )

    def test_dashboard_requires_auth(self):
        self.client.force_authenticate(None)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_counts_by_status(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        counts = response.data["counts_by_status"]
        base = self.baseline["counts_by_status"]
        self.assertEqual(counts["assigned"] - base["assigned"], 1)
        self.assertEqual(counts["retired"] - base["retired"], 1)
        self.assertEqual(counts["available"] - base["available"], 2)

    def test_counts_by_category(self):
        response = self.client.get(reverse("dashboard"))
        counts = response.data["counts_by_category"]
        base = self.baseline["counts_by_category"]
        self.assertEqual(counts["laptop"] - base["laptop"], 2)
        self.assertEqual(counts["monitor"] - base["monitor"], 1)
        self.assertEqual(counts["phone"] - base["phone"], 1)
        self.assertEqual(counts["peripheral"] - base["peripheral"], 0)
        self.assertEqual(counts["other"] - base["other"], 0)

    def test_employees_with_assets(self):
        response = self.client.get(reverse("dashboard"))
        rows = {row["name"]: row["asset_count"] for row in response.data["employees_with_assets"]}
        self.assertEqual(rows.get("Alice"), 1)
        self.assertEqual(rows.get("Bob"), 1, "Bob still has physical custody of the retired asset")

    def test_never_assigned_assets(self):
        response = self.client.get(reverse("dashboard"))
        tags = {row["asset_tag"] for row in response.data["never_assigned_assets"]}
        self.assertIn("D-0004", tags)
        self.assertNotIn("D-0001", tags)
        self.assertNotIn("D-0002", tags)
        self.assertNotIn("D-0003", tags)
