from django.db import models
from django.db.models import Q

from apps.employees.models import Employee


class Asset(models.Model):
    """A piece of equipment the org owns and can hand out to employees.

    ``status`` is NOT stored - it is derived from ``is_retired`` and whether
    the asset currently has an open (unreturned) AssetAssignment. Precedence,
    from highest to lowest:

        1. retired   - ``is_retired`` is True. This wins even if the asset
                       still has an open assignment, representing an asset
                       that has been pulled from service (e.g. broken,
                       lost, decommissioned) without necessarily having gone
                       through a formal return first.
        2. assigned  - no retirement, but there is an AssetAssignment for
                       this asset with ``returned_date IS NULL``.
        3. available - neither of the above.

    See ``Asset.status`` below.
    """

    class Category(models.TextChoices):
        LAPTOP = "laptop", "Laptop"
        MONITOR = "monitor", "Monitor"
        PHONE = "phone", "Phone"
        PERIPHERAL = "peripheral", "Peripheral"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ASSIGNED = "assigned", "Assigned"
        RETIRED = "retired", "Retired"

    asset_tag = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=Category.choices)
    serial_number = models.CharField(max_length=100, blank=True, default="")
    purchase_date = models.DateField(null=True, blank=True)
    is_retired = models.BooleanField(
        default=False,
        help_text="Manually marked retired by the admin. Takes precedence over any open assignment.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["asset_tag"]

    def __str__(self):
        return f"{self.asset_tag} - {self.name}"

    @property
    def open_assignment(self):
        """Returns the current open AssetAssignment, if any. Where the
        queryset was built with ``.prefetch_related("assignments")`` this
        reads from the prefetch cache instead of issuing a new query."""
        for assignment in self.assignments.all():
            if assignment.returned_date is None:
                return assignment
        return None

    @property
    def status(self) -> str:
        if self.is_retired:
            return self.Status.RETIRED
        if self.open_assignment is not None:
            return self.Status.ASSIGNED
        return self.Status.AVAILABLE


class AssetAssignment(models.Model):
    """One stint of an asset being checked out to an employee.

    At most one OPEN assignment (``returned_date IS NULL``) may exist per
    asset at a time - enforced by the partial unique constraint below, and
    backed up by an application-level check inside a transaction in the
    assign view/serializer so a violation surfaces as a clean 400/409
    instead of a raw IntegrityError.
    """

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT, related_name="assignments")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="assignments")
    assigned_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assigned_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["asset"],
                condition=Q(returned_date__isnull=True),
                name="unique_open_assignment_per_asset",
            ),
        ]

    def __str__(self):
        return f"{self.asset.asset_tag} -> {self.employee.name} ({self.assigned_date})"

    @property
    def is_open(self) -> bool:
        return self.returned_date is None
