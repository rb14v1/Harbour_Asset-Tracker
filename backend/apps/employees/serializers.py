from rest_framework import serializers

from apps.employees.models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "email",
            "department",
            "job_title",
            "hire_date",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
