from datetime import date

from rest_framework import serializers

from apps.assets.models import Asset, AssetAssignment
from apps.employees.models import Employee


class AssetSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Asset.Status.choices, read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "asset_tag",
            "name",
            "category",
            "serial_number",
            "purchase_date",
            "is_retired",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class AssetAssignmentSerializer(serializers.ModelSerializer):
    asset_tag = serializers.CharField(source="asset.asset_tag", read_only=True)
    asset_name = serializers.CharField(source="asset.name", read_only=True)
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = AssetAssignment
        fields = [
            "id",
            "asset",
            "asset_tag",
            "asset_name",
            "employee",
            "employee_name",
            "assigned_date",
            "returned_date",
            "notes",
            "is_open",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AssignAssetSerializer(serializers.Serializer):
    """Input serializer for POST /api/assets/{id}/assign/."""

    employee_id = serializers.PrimaryKeyRelatedField(
        source="employee", queryset=Employee.objects.all()
    )
    assigned_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_assigned_date(self, value):
        return value

    def validate(self, attrs):
        attrs.setdefault("assigned_date", date.today())
        return attrs


class ReturnAssignmentSerializer(serializers.Serializer):
    """Input serializer for POST /api/assignments/{id}/return/."""

    returned_date = serializers.DateField(required=False)

    def validate(self, attrs):
        attrs.setdefault("returned_date", date.today())
        return attrs
