from django.db import models


class Vendor(models.Model):
    SERVICE_CATERING = "CATERING"
    SERVICE_DECORATION = "DECORATION"
    SERVICE_PHOTOGRAPHY = "PHOTOGRAPHY"
    SERVICE_VIDEOGRAPHY = "VIDEOGRAPHY"
    SERVICE_MUSIC = "MUSIC"
    SERVICE_MAKEUP = "MAKEUP"
    SERVICE_DRESS = "DRESS"
    SERVICE_VENUE = "VENUE"
    SERVICE_TRANSPORT = "TRANSPORT"
    SERVICE_PRIEST = "PRIEST"
    SERVICE_OTHER = "OTHER"

    SERVICE_CHOICES = (
        (SERVICE_CATERING, "Catering"),
        (SERVICE_DECORATION, "Decoration"),
        (SERVICE_PHOTOGRAPHY, "Photography"),
        (SERVICE_VIDEOGRAPHY, "Videography"),
        (SERVICE_MUSIC, "Music / DJ"),
        (SERVICE_MAKEUP, "Makeup"),
        (SERVICE_DRESS, "Bridal / Groom Wear"),
        (SERVICE_VENUE, "Venue"),
        (SERVICE_TRANSPORT, "Transport"),
        (SERVICE_PRIEST, "Priest / Officiant"),
        (SERVICE_OTHER, "Other"),
    )

    name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=30, choices=SERVICE_CHOICES)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_vendors",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"


class Collaboration(models.Model):
    TYPE_PHOTOGRAPHER = "PHOTOGRAPHER"
    TYPE_VENUE = "VENUE"
    TYPE_CATERER = "CATERER"
    TYPE_DECORATOR = "DECORATOR"
    TYPE_PLANNER = "PLANNER"
    TYPE_INFLUENCER = "INFLUENCER"
    TYPE_OTHER = "OTHER"

    TYPE_CHOICES = (
        (TYPE_PHOTOGRAPHER, "Photographer"),
        (TYPE_VENUE, "Venue"),
        (TYPE_CATERER, "Caterer"),
        (TYPE_DECORATOR, "Decorator"),
        (TYPE_PLANNER, "Planner"),
        (TYPE_INFLUENCER, "Influencer"),
        (TYPE_OTHER, "Other"),
    )

    partner_name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    commission_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Referral commission %",
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        "accounts.Staff",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="created_collaborations",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["partner_name"]

    def __str__(self):
        return f"{self.partner_name} ({self.get_partner_type_display()})"
