from django.db import models


class Task(models.Model):
    PRIORITY_LOW = "LOW"
    PRIORITY_MED = "MED"
    PRIORITY_HIGH = "HIGH"
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MED, "Medium"),
        (PRIORITY_HIGH, "High"),
    )

    STATUS_PENDING = "PENDING"
    STATUS_ONGOING = "ONGOING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_ONGOING, "Ongoing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assigned_to = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="tasks",
    )

    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_MED)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_tasks",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "due_date", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if not self.due_date:
            return False
        if self.status in (self.STATUS_COMPLETED, self.STATUS_CANCELLED):
            return False
        return self.due_date < timezone.now().date()
