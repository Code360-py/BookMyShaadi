from django.core.management.base import BaseCommand

from events.models import GalleryImage
from vendors.models import Vendor


VENDORS = [
    {
        "name": "Marigold Atelier",
        "service_type": Vendor.SERVICE_DECORATION,
        "address": "Jaipur, Rajasthan",
        "notes": "Ceremony mandaps, floral styling and reception decor.",
    },
    {
        "name": "The Saffron Table",
        "service_type": Vendor.SERVICE_CATERING,
        "address": "Mumbai, Maharashtra",
        "notes": "Seasonal menus inspired by regional Indian cuisines.",
    },
    {
        "name": "Everafter Frames",
        "service_type": Vendor.SERVICE_PHOTOGRAPHY,
        "address": "Delhi, NCR",
        "notes": "Candid wedding, portrait and celebration photography.",
    },
    {
        "name": "Ribbon & Reel Films",
        "service_type": Vendor.SERVICE_VIDEOGRAPHY,
        "address": "Hyderabad, Telangana",
        "notes": "Wedding films, highlight edits and event coverage.",
    },
    {
        "name": "House of Hues",
        "service_type": Vendor.SERVICE_MAKEUP,
        "address": "Bengaluru, Karnataka",
        "notes": "Bridal makeup, family styling and trial sessions.",
    },
    {
        "name": "Raag & Rhythm",
        "service_type": Vendor.SERVICE_MUSIC,
        "address": "Pune, Maharashtra",
        "notes": "Live music and DJ sets for every part of the celebration.",
    },
    {
        "name": "The Courtyard Collection",
        "service_type": Vendor.SERVICE_VENUE,
        "address": "Udaipur, Rajasthan",
        "notes": "Garden and heritage-style spaces for intimate gatherings.",
    },
    {
        "name": "The Bridal Edit",
        "service_type": Vendor.SERVICE_DRESS,
        "address": "Chennai, Tamil Nadu",
        "notes": "Bridal and occasion wear with fitting support.",
    },
    {
        "name": "Saat Saath Journeys",
        "service_type": Vendor.SERVICE_TRANSPORT,
        "address": "Goa",
        "notes": "Guest transfers and wedding-day transport coordination.",
    },
]


GALLERY = [
    {
        "title": "Marigold mandap",
        "category": "Ceremony | Photo: The Decor Seo / Unsplash",
        "image_url": "https://images.unsplash.com/photo-1729237261107-6fc4279f6d1c?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "title": "Mehndi and heirloom bangles",
        "category": "Details | Photo: Prateek Jaiswal / Unsplash",
        "image_url": "https://images.unsplash.com/photo-1710494424739-8adc1448e87d?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "title": "A room ready for the celebration",
        "category": "Reception | Photo via Unsplash",
        "image_url": "https://images.unsplash.com/photo-1665607437981-973dcd6a22bb?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "title": "Bridal portrait in red and gold",
        "category": "Portrait | Photo via Unsplash",
        "image_url": "https://images.unsplash.com/photo-1640745691934-1403879c3ae6?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "title": "Wedding finery and warm lights",
        "category": "Portrait | Photo: Royal Photography / Unsplash",
        "image_url": "https://images.unsplash.com/photo-1757598080164-82b5a3e5e234?auto=format&fit=crop&w=1400&q=85",
    },
    {
        "title": "A moment before the ceremony",
        "category": "Portrait | Photo: Raju Kumar / Unsplash",
        "image_url": "https://images.unsplash.com/photo-1695972774868-c43c29717945?auto=format&fit=crop&w=1400&q=85",
    },
]


class Command(BaseCommand):
    help = "Seed sample public vendor listings and wedding gallery images"

    def handle(self, *args, **options):
        for vendor_data in VENDORS:
            vendor, created = Vendor.objects.update_or_create(
                name=vendor_data["name"],
                defaults={**vendor_data, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} vendor: {vendor.name}"))

        for image_data in GALLERY:
            image, created = GalleryImage.objects.update_or_create(
                title=image_data["title"],
                defaults={**image_data, "is_active": True},
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} gallery image: {image.title}"))
