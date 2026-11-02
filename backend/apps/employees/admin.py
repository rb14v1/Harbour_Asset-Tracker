from django.contrib import admin

from apps.employees.models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "department", "job_title", "is_active"]
    search_fields = ["name", "email", "department"]
    list_filter = ["department", "is_active"]
