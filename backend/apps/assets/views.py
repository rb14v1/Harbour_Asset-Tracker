from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.assets.models import Asset, AssetAssignment
from apps.assets.serializers import (
    AssetAssignmentSerializer,
    AssetSerializer,
    AssignAssetSerializer,
    ReturnAssignmentSerializer,
)


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all().prefetch_related("assignments__employee")
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["asset_tag", "name", "serial_number"]
    ordering_fields = ["asset_tag", "name", "purchase_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        status_param = self.request.query_params.get("status")
        if category:
            qs = qs.filter(category=category)
        if status_param in Asset.Status.values:
            # status is a derived property, not a DB column, so for this
            # small-scale demo app it's simplest and clearest to filter in
            # Python rather than reimplement the precedence rules in SQL.
            ids = [a.id for a in qs if a.status == status_param]
            qs = Asset.objects.filter(id__in=ids).prefetch_related("assignments__employee")
        return qs

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "This asset has assignment history and cannot be deleted. "
                            "Retire it instead to pull it from service."},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Create a new open AssetAssignment for this asset. Fails with 409
        if the asset is retired or already has an open assignment."""
        asset = self.get_object()
        serializer = AssignAssetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.validated_data["employee"]
        assigned_date = serializer.validated_data["assigned_date"]
        notes = serializer.validated_data.get("notes", "")

        try:
            with transaction.atomic():
                asset.refresh_from_db()
                if asset.is_retired:
                    return Response(
                        {"detail": "Cannot assign a retired asset."},
                        status=status.HTTP_409_CONFLICT,
                    )
                if AssetAssignment.objects.filter(asset=asset, returned_date__isnull=True).exists():
                    return Response(
                        {"detail": "This asset already has an open assignment. Return it before reassigning."},
                        status=status.HTTP_409_CONFLICT,
                    )
                assignment = AssetAssignment.objects.create(
                    asset=asset, employee=employee, assigned_date=assigned_date, notes=notes
                )
        except IntegrityError:
            # Backstop for a race between the check above and the insert -
            # the partial unique constraint on AssetAssignment is the real
            # source of truth here.
            return Response(
                {"detail": "This asset already has an open assignment. Return it before reassigning."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(AssetAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def retire(self, request, pk=None):
        """Marks the asset retired. This does NOT touch any open
        assignment - retirement takes precedence over assignment in the
        derived status (see Asset docstring), representing equipment pulled
        from service, with or without a formal return on record."""
        asset = self.get_object()
        asset.is_retired = True
        asset.save(update_fields=["is_retired"])
        return Response(AssetSerializer(asset).data)

    @action(detail=True, methods=["post"])
    def unretire(self, request, pk=None):
        asset = self.get_object()
        asset.is_retired = False
        asset.save(update_fields=["is_retired"])
        return Response(AssetSerializer(asset).data)


class AssetAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """Assignment history is only ever created through
    POST /api/assets/{id}/assign/ so the one-open-assignment invariant has a
    single enforcement point. This viewset is read (+ return) only."""

    queryset = AssetAssignment.objects.select_related("asset", "employee").all()
    serializer_class = AssetAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["asset", "employee"]
    ordering_fields = ["assigned_date", "returned_date", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        open_param = self.request.query_params.get("open")
        if open_param is not None:
            is_open = open_param.lower() in ("1", "true", "yes")
            qs = qs.filter(returned_date__isnull=is_open)
        return qs

    @action(detail=True, methods=["post"], url_path="return", url_name="return")
    def return_asset(self, request, pk=None):
        assignment = self.get_object()
        if not assignment.is_open:
            return Response(
                {"detail": "This assignment has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ReturnAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        returned_date = serializer.validated_data["returned_date"]
        if returned_date < assignment.assigned_date:
            return Response(
                {"detail": "returned_date cannot be before assigned_date."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        assignment.returned_date = returned_date
        assignment.save(update_fields=["returned_date"])
        return Response(AssetAssignmentSerializer(assignment).data)
