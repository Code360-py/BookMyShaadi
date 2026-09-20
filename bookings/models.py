from django.db import models


class Enquiry(models.Model):
    STATUS_NEW = "NEW"
    STATUS_CONTACTED = "CONTACTED"
    STATUS_CONVERTED = "CONVERTED"
    STATUS_CLOSED = "CLOSED"
    STATUS_CHOICES = (
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_CONVERTED, "Converted"),
        (STATUS_CLOSED, "Closed"),
    )

    # submitter info (no login required)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    event_date = models.DateField(null=True, blank=True)
    event_type = models.CharField(
        max_length=50,
        choices=(
            ("WEDDING", "Wedding"),
            ("ENGAGEMENT", "Engagement"),
            ("BIRTHDAY", "Birthday"),
            ("CORPORATE", "Corporate"),
            ("OTHER", "Other"),
        ),
        default="WEDDING",
    )
    guests = models.PositiveIntegerField(null=True, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    handled_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="enquiries_handled",
    )
    converted_customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="source_enquiries",
    )

    # anti-spam / forensics
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}> ({self.status})"


class Booking(models.Model):
    TYPE_CONSULT = "CONSULT"
    TYPE_SITE_VISIT = "SITE_VISIT"
    TYPE_FOLLOWUP = "FOLLOWUP"
    TYPE_OTHER = "OTHER"
    TYPE_CHOICES = (
        (TYPE_CONSULT, "Consultation"),
        (TYPE_SITE_VISIT, "Site visit"),
        (TYPE_FOLLOWUP, "Follow-up"),
        (TYPE_OTHER, "Other"),
    )

    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_DONE = "DONE"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_NO_SHOW = "NO_SHOW"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_DONE, "Done"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_NO_SHOW, "No-show"),
    )

    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    booking_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=TYPE_CONSULT
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    assigned_to = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_bookings",
    )
    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_bookings",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"{self.customer.full_name} — {self.get_booking_type_display()} @ {self.scheduled_at:%d %b %Y %H:%M}"
