from django.contrib import admin

from apps.assets.models import Asset, AssetAssignment


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ["asset_tag", "name", "category", "is_retired", "status"]
    search_fields = ["asset_tag", "name", "serial_number"]
    list_filter = ["category", "is_retired"]

    def status(self, obj):
        return obj.status


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ["asset", "employee", "assigned_date", "returned_date"]
    list_filter = ["returned_date"]
    search_fields = ["asset__asset_tag", "employee__name"]
