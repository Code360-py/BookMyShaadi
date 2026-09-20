from django.db import models


class Event(models.Model):
    TYPE_WEDDING = "WEDDING"
    TYPE_ENGAGEMENT = "ENGAGEMENT"
    TYPE_BIRTHDAY = "BIRTHDAY"
    TYPE_CORPORATE = "CORPORATE"
    TYPE_OTHER = "OTHER"
    TYPE_CHOICES = (
        (TYPE_WEDDING, "Wedding"),
        (TYPE_ENGAGEMENT, "Engagement"),
        (TYPE_BIRTHDAY, "Birthday"),
        (TYPE_CORPORATE, "Corporate"),
        (TYPE_OTHER, "Other"),
    )

    STATUS_PLANNING = "PLANNING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_ONGOING = "ONGOING"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = (
        (STATUS_PLANNING, "Planning"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_ONGOING, "Ongoing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_WEDDING)
    customer = models.ForeignKey(
        "accounts.Customer",
        on_delete=models.PROTECT,
        related_name="events",
    )

    bride_name = models.CharField(max_length=255, blank=True)
    groom_name = models.CharField(max_length=255, blank=True)

    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255)
    guest_count = models.PositiveIntegerField(null=True, blank=True)

    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNING)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_events",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"

    @property
    def total_expenses(self):
        agg = self.expenses.aggregate(models.Sum("amount"))["amount__sum"]
        return agg or 0

    @property
    def total_payments(self):
        agg = self.payments.filter(direction="IN").aggregate(models.Sum("amount"))["amount__sum"]
        return agg or 0

    @property
    def remaining_budget(self):
        return self.budget - self.total_expenses


class Package(models.Model):
    """Service tier shown on the public site."""

    slug = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    price_from = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text="One feature per line.")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "price_from"]

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [line.strip() for line in (self.features or "").splitlines() if line.strip()]


class GalleryImage(models.Model):
    """Public gallery."""

    title = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True)
    image = models.ImageField(upload_to="gallery/", blank=True, null=True)
    category = models.CharField(max_length=50, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title or f"Image #{self.pk}"

    @property
    def src(self):
        if self.image:
            return self.image.url
        return self.image_url
