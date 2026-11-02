from django.db.models import ProtectedError
from rest_framework import permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.employees.models import Employee
from apps.employees.serializers import EmployeeSerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ["department", "is_active"]
    search_fields = ["name", "email", "department", "job_title"]
    ordering_fields = ["name", "hire_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        department = self.request.query_params.get("department")
        is_active = self.request.query_params.get("is_active")
        if department:
            qs = qs.filter(department__iexact=department)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        return qs

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This employee has asset assignment history and cannot be deleted. "
                            "Return their assets first, or mark the employee inactive instead."},
                status=status.HTTP_409_CONFLICT,
            )
