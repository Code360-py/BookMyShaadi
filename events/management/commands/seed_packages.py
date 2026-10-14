from django.core.management.base import BaseCommand

from events.models import Package


PACKAGES = [
    dict(slug="silver", name="Silver", tagline="Essential planning for intimate weddings",
         price_from=50000, sort_order=1,
         features="Venue shortlist\nVendor recommendations\nDay-of coordination\nBasic décor guidance"),
    dict(slug="gold", name="Gold", tagline="Full planning for 150–300 guests",
         price_from=150000, sort_order=2, is_featured=True,
         features="Everything in Silver\nDedicated planner\nFull vendor coordination\nDécor & stage design\nOn-day team of 3"),
    dict(slug="platinum", name="Platinum", tagline="End-to-end luxury experience",
         price_from=400000, sort_order=3,
         features="Everything in Gold\nDestination coordination\nGuest stay & transport\nBridal styling team\nCustom décor & lighting\n24×7 single point of contact"),
]


class Command(BaseCommand):
    help = "Seed default service packages"

    def handle(self, *args, **opts):
        for p in PACKAGES:
            obj, created = Package.objects.update_or_create(
                slug=p["slug"], defaults=p,
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'Created' if created else 'Updated'}: {obj.name}")
            )
