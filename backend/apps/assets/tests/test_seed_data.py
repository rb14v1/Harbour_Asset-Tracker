"""Verifies the row counts produced by the 0002_seed_demo_data data
migration. Since migrations (including data migrations) run as part of
building the test database, this is a plain assertion against the
as-migrated state - no fixtures are created in this test.
"""
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assets.models import Asset, AssetAssignment
from apps.employees.models import Employee


class SeedDataMigrationTests(APITestCase):
    def test_demo_admin_user_created(self):
        admin = User.objects.get(email="admin@example.com")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password("demo12345"))

    def test_employee_count_and_departments(self):
        self.assertEqual(Employee.objects.count(), 6)
        departments = set(Employee.objects.values_list("department", flat=True))
        self.assertGreaterEqual(len(departments), 2)
        self.assertEqual(Employee.objects.filter(is_active=False).count(), 1)

    def test_asset_count_and_categories(self):
        self.assertGreaterEqual(Asset.objects.count(), 8)
        self.assertLessEqual(Asset.objects.count(), 10)
        categories = set(Asset.objects.values_list("category", flat=True))
        self.assertGreaterEqual(len(categories), 3)
        self.assertEqual(Asset.objects.filter(is_retired=True).count(), 1)

    def test_assignment_history_has_open_and_returned_rows(self):
        self.assertGreater(AssetAssignment.objects.filter(returned_date__isnull=True).count(), 0)
        self.assertGreater(AssetAssignment.objects.filter(returned_date__isnull=False).count(), 0)

    def test_at_least_one_asset_never_assigned(self):
        never_assigned = Asset.objects.exclude(id__in=AssetAssignment.objects.values("asset_id"))
        self.assertGreaterEqual(never_assigned.count(), 1)

    def test_retired_asset_status_precedence_in_seed_data(self):
        """AT-1003 is seeded retired AND with an open assignment - confirms
        the precedence rule holds for real seed data, not just unit-test
        fixtures."""
        retired_asset = Asset.objects.get(asset_tag="AT-1003")
        self.assertTrue(retired_asset.is_retired)
        self.assertIsNotNone(retired_asset.open_assignment)
        self.assertEqual(retired_asset.status, Asset.Status.RETIRED)

    def test_seed_migration_is_idempotent_on_rerun(self):
        """Re-invoking the seed function directly (simulating a repeat
        `migrate`) must not create duplicate rows."""
        import importlib.util

        from django.apps import apps as real_apps
        from django.db import connection

        import os

        module_path = os.path.join(
            os.path.dirname(__file__), "..", "migrations", "0002_seed_demo_data.py"
        )
        spec = importlib.util.spec_from_file_location("seed_migration_rerun_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        before = (User.objects.count(), Employee.objects.count(), Asset.objects.count(), AssetAssignment.objects.count())
        module.seed_demo_data(real_apps, connection)
        after = (User.objects.count(), Employee.objects.count(), Asset.objects.count(), AssetAssignment.objects.count())

        self.assertEqual(before, after)
