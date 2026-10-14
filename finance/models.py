from django.db import models


class Expense(models.Model):
    CAT_FOOD = "FOOD"
    CAT_DECOR = "DECOR"
    CAT_PHOTOGRAPHY = "PHOTOGRAPHY"
    CAT_VIDEOGRAPHY = "VIDEOGRAPHY"
    CAT_MUSIC = "MUSIC"
    CAT_MAKEUP = "MAKEUP"
    CAT_DRESS = "DRESS"
    CAT_VENUE = "VENUE"
    CAT_TRANSPORT = "TRANSPORT"
    CAT_RENTAL = "RENTAL"
    CAT_STAFF = "STAFF"
    CAT_MISC = "MISC"
    CATEGORY_CHOICES = (
        (CAT_FOOD, "Food / Catering"),
        (CAT_DECOR, "Decoration"),
        (CAT_PHOTOGRAPHY, "Photography"),
        (CAT_VIDEOGRAPHY, "Videography"),
        (CAT_MUSIC, "Music / DJ"),
        (CAT_MAKEUP, "Makeup"),
        (CAT_DRESS, "Bridal / Groom Wear"),
        (CAT_VENUE, "Venue"),
        (CAT_TRANSPORT, "Transport"),
        (CAT_RENTAL, "Rentals"),
        (CAT_STAFF, "Staff / Labour"),
        (CAT_MISC, "Miscellaneous"),
    )

    STATUS_PENDING = "PENDING"
    STATUS_PARTIAL = "PARTIAL"
    STATUS_PAID = "PAID"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PARTIAL, "Partial"),
        (STATUS_PAID, "Paid"),
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="expenses",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="expenses",
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CAT_MISC)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    date = models.DateField()
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_expenses",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} — {self.amount}"


class Payment(models.Model):
    DIRECTION_IN = "IN"
    DIRECTION_OUT = "OUT"
    DIRECTION_CHOICES = (
        (DIRECTION_IN, "Received (from customer)"),
        (DIRECTION_OUT, "Paid (to vendor)"),
    )

    METHOD_CASH = "CASH"
    METHOD_UPI = "UPI"
    METHOD_BANK = "BANK"
    METHOD_CARD = "CARD"
    METHOD_CHEQUE = "CHEQUE"
    METHOD_OTHER = "OTHER"
    METHOD_CHOICES = (
        (METHOD_CASH, "Cash"),
        (METHOD_UPI, "UPI"),
        (METHOD_BANK, "Bank Transfer"),
        (METHOD_CARD, "Card"),
        (METHOD_CHEQUE, "Cheque"),
        (METHOD_OTHER, "Other"),
    )

    STATUS_PENDING = "PENDING"
    STATUS_CLEARED = "CLEARED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CLEARED, "Cleared"),
        (STATUS_FAILED, "Failed"),
    )

    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="payments",
    )
    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="payments",
        help_text="Only for outgoing payments.",
    )

    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES, default=DIRECTION_IN)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, default=METHOD_CASH)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CLEARED)
    reference_no = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_direction_display()} — {self.amount} ({self.get_method_display()})"
