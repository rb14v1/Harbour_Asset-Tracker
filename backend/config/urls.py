from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.auth_urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/employees/", include("apps.employees.urls")),
    path("api/", include("apps.assets.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
]
