from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assets.models import Asset
from apps.employees.models import Employee


class DashboardView(APIView):
    """A one-shot summary view for the admin landing page. Deliberately
    computed in plain Python rather than heavy ORM aggregation - the data
    volumes in this app are small (dozens to low hundreds of rows), so
    clarity wins over query-count optimisation."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        assets = list(Asset.objects.all().prefetch_related("assignments__employee"))

        counts_by_status = {choice: 0 for choice in Asset.Status.values}
        counts_by_category = {choice: 0 for choice in Asset.Category.values}
        never_assigned = []

        for asset in assets:
            counts_by_status[asset.status] += 1
            counts_by_category[asset.category] += 1
            if not asset.assignments.all():
                never_assigned.append(asset)

        employees_with_assets = {}
        for asset in assets:
            open_assignment = asset.open_assignment
            if open_assignment is None:
                continue
            employee = open_assignment.employee
            entry = employees_with_assets.setdefault(
                employee.id, {"employee_id": employee.id, "name": employee.name, "asset_count": 0}
            )
            entry["asset_count"] += 1

        return Response({
            "counts_by_status": counts_by_status,
            "counts_by_category": counts_by_category,
            "employees_with_assets": sorted(
                employees_with_assets.values(), key=lambda row: row["name"]
            ),
            "never_assigned_assets": [
                {"id": a.id, "asset_tag": a.asset_tag, "name": a.name, "category": a.category}
                for a in sorted(never_assigned, key=lambda a: a.asset_tag)
            ],
        })
