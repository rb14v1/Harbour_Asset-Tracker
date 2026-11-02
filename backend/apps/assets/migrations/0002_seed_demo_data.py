"""Demo-data seed migration.

Creates one demo admin user, a handful of employees, a spread of assets
across every category (including one retired), and assignment history -
some open (currently in use), some returned, with at least a couple of
assets that have never been assigned at all (useful for spotting
underutilized stock on the dashboard).

Idempotent by design: every lookup is keyed on a real unique field
(User.email, Employee.email, Asset.asset_tag) via get_or_create, and
AssetAssignment rows are keyed on (asset, employee, assigned_date) via
get_or_create too, so running `migrate` again - e.g. after a fresh
`migrate --fake` reset, or just re-running the full migration history - does
not insert duplicate rows.
"""
from datetime import date

from django.db import migrations


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Employee = apps.get_model("employees", "Employee")
    Asset = apps.get_model("assets", "Asset")
    AssetAssignment = apps.get_model("assets", "AssetAssignment")

    # --- Admin user -----------------------------------------------------
    admin, created = User.objects.get_or_create(
        email="admin@example.com",
        defaults={
            "first_name": "Demo",
            "last_name": "Admin",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    if created:
        # set_password() isn't available on the historical model, so hash
        # the password the same way Django's auth system does.
        from django.contrib.auth.hashers import make_password

        admin.password = make_password("demo12345")
        admin.save(using=schema_editor.connection.alias)

    # --- Employees --------------------------------------------------------
    employees_data = [
        dict(name="Alice Johnson", email="alice.johnson@example.com", department="Engineering",
             job_title="Software Engineer", hire_date=date(2021, 3, 15), is_active=True),
        dict(name="Bob Smith", email="bob.smith@example.com", department="Engineering",
             job_title="QA Engineer", hire_date=date(2022, 7, 1), is_active=True),
        dict(name="Carol Davis", email="carol.davis@example.com", department="Sales",
             job_title="Account Executive", hire_date=date(2020, 11, 20), is_active=True),
        dict(name="David Lee", email="david.lee@example.com", department="Sales",
             job_title="Sales Manager", hire_date=date(2019, 5, 10), is_active=True),
        dict(name="Priya Patel", email="priya.patel@example.com", department="HR",
             job_title="HR Generalist", hire_date=date(2023, 1, 9), is_active=True),
        dict(name="Ethan Brown", email="ethan.brown@example.com", department="IT",
             job_title="IT Support Specialist", hire_date=date(2022, 9, 12), is_active=False),
    ]
    employees = {}
    for data in employees_data:
        email = data.pop("email")
        employee, _ = Employee.objects.get_or_create(email=email, defaults=data)
        employees[email] = employee

    # --- Assets -------------------------------------------------------
    assets_data = [
        dict(asset_tag="AT-1001", name='MacBook Pro 14"', category="laptop",
             serial_number="SN-MBP-1001", purchase_date=date(2022, 1, 10), is_retired=False),
        dict(asset_tag="AT-1002", name="Dell Latitude 5420", category="laptop",
             serial_number="SN-DL-1002", purchase_date=date(2021, 6, 15), is_retired=False),
        dict(asset_tag="AT-1003", name="Lenovo ThinkPad X1", category="laptop",
             serial_number="SN-LT-1003", purchase_date=date(2023, 2, 20), is_retired=True),
        dict(asset_tag="AT-2001", name='Dell UltraSharp 27" Monitor', category="monitor",
             serial_number="SN-MON-2001", purchase_date=date(2021, 8, 1), is_retired=False),
        dict(asset_tag="AT-2002", name='LG 24" Monitor', category="monitor",
             serial_number="SN-MON-2002", purchase_date=date(2022, 3, 11), is_retired=False),
        dict(asset_tag="AT-3001", name="iPhone 13", category="phone",
             serial_number="SN-PH-3001", purchase_date=date(2022, 11, 5), is_retired=False),
        dict(asset_tag="AT-3002", name="Samsung Galaxy S21", category="phone",
             serial_number="SN-PH-3002", purchase_date=date(2021, 10, 18), is_retired=False),
        dict(asset_tag="AT-4001", name="Logitech MX Master 3 Mouse", category="peripheral",
             serial_number="", purchase_date=date(2023, 1, 1), is_retired=False),
        dict(asset_tag="AT-4002", name="Keychron K2 Keyboard", category="peripheral",
             serial_number="", purchase_date=None, is_retired=False),
        dict(asset_tag="AT-5001", name="USB-C Docking Station", category="other",
             serial_number="SN-DOCK-5001", purchase_date=date(2022, 5, 30), is_retired=False),
    ]
    assets = {}
    for data in assets_data:
        tag = data.pop("asset_tag")
        asset, _ = Asset.objects.get_or_create(asset_tag=tag, defaults=data)
        assets[tag] = asset

    # --- Assignments ----------------------------------------------------
    # (asset_tag, employee_email, assigned_date, returned_date, notes)
    assignments_data = [
        ("AT-1001", "alice.johnson@example.com", date(2022, 1, 15), None, "Onboarding laptop"),
        ("AT-4001", "alice.johnson@example.com", date(2022, 1, 15), None, "Onboarding peripheral"),
        ("AT-1002", "bob.smith@example.com", date(2021, 6, 20), None, ""),
        # AT-1003 is retired but still shows an open assignment on record -
        # demonstrates that retired takes precedence over assigned in the
        # derived Asset.status (see apps/assets/models.py).
        ("AT-1003", "david.lee@example.com", date(2023, 3, 1), None, "Screen cracked; pulled from service"),
        ("AT-2001", "priya.patel@example.com", date(2023, 1, 10), None, ""),
        ("AT-2002", "ethan.brown@example.com", date(2022, 9, 15), date(2023, 5, 1), "Returned on role change"),
        ("AT-3001", "carol.davis@example.com", date(2022, 11, 10), None, ""),
        ("AT-3002", "alice.johnson@example.com", date(2021, 10, 20), date(2022, 1, 10), "Replaced by AT-1001 bundle"),
        # AT-4002 and AT-5001 are deliberately never assigned - underutilized
        # stock, surfaced on the dashboard's "never assigned" list.
    ]
    for asset_tag, email, assigned_date, returned_date, notes in assignments_data:
        AssetAssignment.objects.get_or_create(
            asset=assets[asset_tag],
            employee=employees[email],
            assigned_date=assigned_date,
            defaults={"returned_date": returned_date, "notes": notes},
        )


def unseed_demo_data(apps, schema_editor):
    """Reverse migration: best-effort removal of exactly the demo rows this
    migration creates, so `migrate assets 0001` round-trips cleanly."""
    User = apps.get_model("accounts", "User")
    Employee = apps.get_model("employees", "Employee")
    Asset = apps.get_model("assets", "Asset")
    AssetAssignment = apps.get_model("assets", "AssetAssignment")

    asset_tags = [f"AT-{n}" for n in (1001, 1002, 1003, 2001, 2002, 3001, 3002, 4001, 4002, 5001)]
    employee_emails = [
        "alice.johnson@example.com", "bob.smith@example.com", "carol.davis@example.com",
        "david.lee@example.com", "priya.patel@example.com", "ethan.brown@example.com",
    ]

    # Both Asset->AssetAssignment and Employee->AssetAssignment are PROTECT,
    # so assignments must go first.
    AssetAssignment.objects.filter(asset__asset_tag__in=asset_tags).delete()
    Asset.objects.filter(asset_tag__in=asset_tags).delete()
    Employee.objects.filter(email__in=employee_emails).delete()
    User.objects.filter(email="admin@example.com").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("employees", "0001_initial"),
        ("assets", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
