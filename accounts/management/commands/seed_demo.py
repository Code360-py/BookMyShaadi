"""
Seed BookMyShaadi with demo data:
  --staff 100       (1 admin + 10 managers + 89 staff)
  --customers 120
  --enquiries 150
  --bookings 200
  --events 120
  --vendors 100
  --collabs 60
  --tasks 300
  --expenses 400
  --payments 350

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --staff 50 --events 40
    python manage.py seed_demo --wipe        # clear first

All created users get password: demo12345
Admin credentials: admin@bookmyshaadi.local / admin12345
"""

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Customer, Staff
from bookings.models import Booking, Enquiry
from events.models import Event, GalleryImage, Package
from finance.models import Expense, Payment
from tasks.models import Task
from vendors.models import Collaboration, Vendor


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Ananya", "Diya", "Aadhya", "Saanvi", "Pari", "Anika",
    "Navya", "Myra", "Sara", "Aarohi", "Kiara", "Riya", "Isha", "Neha",
    "Priya", "Pooja", "Meera", "Anjali", "Kavya", "Tanvi", "Rohit", "Vikram",
    "Karan", "Rahul", "Siddharth", "Nikhil", "Aryan", "Dev", "Yash", "Harsh",
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Gupta", "Singh",
    "Kumar", "Mehta", "Joshi", "Chopra", "Malhotra", "Kapoor", "Bansal",
    "Rao", "Menon", "Pillai", "Shah", "Desai", "Bhat", "Kulkarni", "Mukherjee",
]

CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Pune", "Kolkata",
    "Ahmedabad", "Jaipur", "Goa", "Kochi", "Lucknow", "Udaipur", "Chandigarh",
]

VENUES = [
    "Taj Palace", "The Leela", "ITC Grand", "Radisson Blu", "JW Marriott",
    "Oberoi", "Novotel", "Hyatt Regency", "The Grand Bhagwati", "Vivanta",
    "Rambagh Palace", "Umaid Bhawan", "Fairmont", "Trident",
]

VENDOR_NAMES = [
    "Royal Caterers", "Bloom Decor", "Lens Studio", "Sound & Light Co",
    "Mehndi Magic", "Bridal Couture", "Glow Makeup Artistry", "Grand Ballroom",
    "Elite Transport", "Sacred Ceremonies", "Frame Films", "Petals & Vows",
    "Shubh Catering", "Dream Events", "Story Weavers", "Candid Clicks",
]

COLLAB_PARTNERS = [
    "WeddingWire", "ShaadiSaga", "The Wedding Brigade", "LBB Weddings",
    "WedMeGood", "The Grand Affair Co", "Elite Planners", "Bloom Studio",
    "Candid Dreams", "City Events", "Royal Hosts", "Aisle Society",
]

TASK_TITLES = [
    "Confirm venue booking", "Pay vendor advance", "Finalize menu",
    "Photographer briefing", "Décor site visit", "Guest list review",
    "Invitation design", "Transport coordination", "Rental pickup",
    "Rehearsal schedule", "Makeup trial", "Outfit fitting",
    "Florist meet", "Catering tasting", "Sound check",
]


def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rand_email(name, n):
    handle = name.lower().replace(" ", ".")
    return f"{handle}{n}@example.com"


def rand_phone():
    return "+91 " + "".join(str(random.randint(0, 9)) for _ in range(10))


def rand_date_within(days_from=-180, days_to=365):
    """Returns a date between N days ago and M days from now."""
    offset = random.randint(days_from, days_to)
    return timezone.now().date() + timedelta(days=offset)


def rand_dt_within(days_from=-60, days_to=90):
    offset = random.randint(days_from, days_to)
    hour = random.choice([10, 11, 13, 15, 17, 18, 19])
    minute = random.choice([0, 15, 30, 45])
    return timezone.now().replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=offset)


class Command(BaseCommand):
    help = "Seed demo data for BookMyShaadi"

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true", help="Delete all existing data first")
        parser.add_argument("--staff", type=int, default=100)
        parser.add_argument("--customers", type=int, default=120)
        parser.add_argument("--enquiries", type=int, default=150)
        parser.add_argument("--bookings", type=int, default=200)
        parser.add_argument("--events", type=int, default=120)
        parser.add_argument("--vendors", type=int, default=100)
        parser.add_argument("--collabs", type=int, default=60)
        parser.add_argument("--tasks", type=int, default=300)
        parser.add_argument("--expenses", type=int, default=400)
        parser.add_argument("--payments", type=int, default=350)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(42)

        if opts["wipe"]:
            self.stdout.write(self.style.WARNING("Wiping existing data..."))
            GalleryImage.objects.all().delete()
            Package.objects.all().delete()
            Payment.objects.all().delete()
            Expense.objects.all().delete()
            Task.objects.all().delete()
            Event.objects.all().delete()
            Booking.objects.all().delete()
            Enquiry.objects.all().delete()
            Vendor.objects.all().delete()
            Collaboration.objects.all().delete()
            Customer.objects.all().delete()
            Staff.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ wiped"))

        # -------------------------------------------------------------------
        # 1. Staff
        # -------------------------------------------------------------------
        admin_email = "admin@bookmyshaadi.local"
        admin = Staff.objects.filter(email=admin_email).first()
        if not admin:
            admin = Staff(full_name="Owner Admin", email=admin_email,
                          role=Staff.ROLE_ADMIN, is_active=True)
            admin.set_password("admin12345")
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"✓ admin created: {admin_email} / admin12345"))

        n = opts["staff"]
        created = 0
        for i in range(n):
            email = f"staff{i+1}@bookmyshaadi.local"
            if Staff.objects.filter(email=email).exists():
                continue
            name = rand_name()
            role = random.choices(
                [Staff.ROLE_MANAGER, Staff.ROLE_STAFF],
                weights=[1, 9],
            )[0]
            s = Staff(
                full_name=name, email=email, phone=rand_phone(),
                role=role, is_active=random.random() > 0.05,
            )
            s.set_password("demo12345")
            s.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"✓ staff: +{created}"))

        all_staff = list(Staff.objects.all())

        # -------------------------------------------------------------------
        # 2. Customers
        # -------------------------------------------------------------------
        n = opts["customers"]
        created = 0
        for i in range(n):
            email = f"customer{i+1}@example.com"
            if Customer.objects.filter(email=email).exists():
                continue
            c = Customer(
                email=email, full_name=rand_name(), phone=rand_phone(),
                is_active=random.random() > 0.03,
                is_email_verified=random.random() > 0.2,
            )
            c.set_password("demo12345")
            c.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"✓ customers: +{created}"))

        all_customers = list(Customer.objects.all())

        # -------------------------------------------------------------------
        # 3. Vendors
        # -------------------------------------------------------------------
        n = opts["vendors"]
        created = 0
        for i in range(n):
            v = Vendor(
                name=f"{random.choice(VENDOR_NAMES)} {i+1}",
                service_type=random.choice([k for k, _ in Vendor.SERVICE_CHOICES]),
                contact_person=rand_name(),
                phone=rand_phone(),
                email=f"vendor{i+1}@vendors.local",
                address=random.choice(CITIES),
                is_active=random.random() > 0.05,
                created_by=random.choice(all_staff) if all_staff else None,
            )
            v.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"✓ vendors: +{created}"))

        all_vendors = list(Vendor.objects.all())

        # -------------------------------------------------------------------
        # 4. Collaborations
        # -------------------------------------------------------------------
        n = opts["collabs"]
        created = 0
        for i in range(n):
            c = Collaboration(
                partner_name=f"{random.choice(COLLAB_PARTNERS)} {i+1}",
                partner_type=random.choice([k for k, _ in Collaboration.TYPE_CHOICES]),
                contact_person=rand_name(),
                phone=rand_phone(),
                email=f"collab{i+1}@partners.local",
                commission_pct=Decimal(random.choice([5, 7.5, 10, 12.5, 15])),
                is_active=random.random() > 0.1,
                created_by=random.choice(all_staff) if all_staff else None,
            )
            c.save()
            created += 1
        self.stdout.write(self.style.SUCCESS(f"✓ collaborations: +{created}"))

        # -------------------------------------------------------------------
        # 5. Enquiries
        # -------------------------------------------------------------------
        n = opts["enquiries"]
        for i in range(n):
            status = random.choices(
                [Enquiry.STATUS_NEW, Enquiry.STATUS_CONTACTED,
                 Enquiry.STATUS_CONVERTED, Enquiry.STATUS_CLOSED],
                weights=[4, 2, 2, 1],
            )[0]
            e = Enquiry.objects.create(
                full_name=rand_name(),
                email=f"lead{i+1}@example.com",
                phone=rand_phone(),
                event_type=random.choice([k for k, _ in Enquiry._meta.get_field("event_type").choices]),
                event_date=rand_date_within(30, 400),
                guests=random.choice([50, 100, 150, 200, 300, 500]),
                budget=Decimal(random.choice([50000, 100000, 200000, 500000, 1000000])),
                message="Looking for a full-service planning team.",
                status=status,
                handled_by=random.choice(all_staff) if status != Enquiry.STATUS_NEW and all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ enquiries: +{n}"))

        # -------------------------------------------------------------------
        # 6. Bookings
        # -------------------------------------------------------------------
        n = opts["bookings"]
        for i in range(n):
            scheduled = rand_dt_within(-90, 90)
            if scheduled > timezone.now():
                status = random.choice([Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED])
            else:
                status = random.choice([Booking.STATUS_DONE, Booking.STATUS_NO_SHOW, Booking.STATUS_CANCELLED])
            Booking.objects.create(
                customer=random.choice(all_customers),
                booking_type=random.choice([k for k, _ in Booking.TYPE_CHOICES]),
                scheduled_at=scheduled,
                duration_minutes=random.choice([30, 45, 60, 90]),
                location=random.choice(CITIES),
                notes="",
                status=status,
                assigned_to=random.choice(all_staff) if all_staff else None,
                created_by=random.choice(all_staff) if all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ bookings: +{n}"))

        # -------------------------------------------------------------------
        # 7. Events
        # -------------------------------------------------------------------
        n = opts["events"]
        for i in range(n):
            customer = random.choice(all_customers)
            date = rand_date_within(-120, 300)
            if date < timezone.now().date():
                status = random.choice([Event.STATUS_COMPLETED, Event.STATUS_CANCELLED])
            else:
                status = random.choice([Event.STATUS_PLANNING, Event.STATUS_CONFIRMED, Event.STATUS_ONGOING])
            Event.objects.create(
                title=f"{random.choice(['Grand', 'Royal', 'Intimate', 'Dream', 'Elegant'])} Wedding #{i+1}",
                event_type=random.choice([k for k, _ in Event.TYPE_CHOICES]),
                customer=customer,
                bride_name=rand_name(),
                groom_name=rand_name(),
                date=date,
                end_date=date + timedelta(days=random.choice([0, 1, 2])),
                location=f"{random.choice(VENUES)}, {random.choice(CITIES)}",
                guest_count=random.choice([80, 150, 250, 400, 600]),
                budget=Decimal(random.choice([300000, 500000, 800000, 1500000, 2500000])),
                status=status,
                notes="",
                created_by=random.choice(all_staff) if all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ events: +{n}"))

        all_events = list(Event.objects.all())

        # -------------------------------------------------------------------
        # 8. Tasks
        # -------------------------------------------------------------------
        n = opts["tasks"]
        for i in range(n):
            event = random.choice(all_events)
            due = event.date - timedelta(days=random.randint(-5, 30))
            if due < timezone.now().date():
                status = random.choice([Task.STATUS_COMPLETED, Task.STATUS_CANCELLED, Task.STATUS_PENDING])
            else:
                status = random.choice([Task.STATUS_PENDING, Task.STATUS_ONGOING])
            Task.objects.create(
                title=random.choice(TASK_TITLES),
                description="",
                event=event,
                assigned_to=random.choice(all_staff) if all_staff else None,
                due_date=due,
                priority=random.choice([Task.PRIORITY_LOW, Task.PRIORITY_MED, Task.PRIORITY_HIGH]),
                status=status,
                created_by=random.choice(all_staff) if all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ tasks: +{n}"))

        # -------------------------------------------------------------------
        # 9. Expenses
        # -------------------------------------------------------------------
        n = opts["expenses"]
        for i in range(n):
            event = random.choice(all_events)
            vendor = random.choice(all_vendors) if random.random() > 0.2 else None
            Expense.objects.create(
                event=event,
                vendor=vendor,
                category=random.choice([k for k, _ in Expense.CATEGORY_CHOICES]),
                description="",
                amount=Decimal(random.randint(5000, 200000)),
                status=random.choice([Expense.STATUS_PENDING, Expense.STATUS_PARTIAL, Expense.STATUS_PAID]),
                date=rand_date_within(-120, 30),
                notes="",
                created_by=random.choice(all_staff) if all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ expenses: +{n}"))

        # -------------------------------------------------------------------
        # 10. Payments
        # -------------------------------------------------------------------
        n = opts["payments"]
        for i in range(n):
            event = random.choice(all_events)
            direction = random.choices(
                [Payment.DIRECTION_IN, Payment.DIRECTION_OUT],
                weights=[6, 4],
            )[0]
            vendor = random.choice(all_vendors) if direction == Payment.DIRECTION_OUT else None
            Payment.objects.create(
                event=event,
                vendor=vendor,
                direction=direction,
                amount=Decimal(random.randint(10000, 500000)),
                method=random.choice([k for k, _ in Payment.METHOD_CHOICES]),
                status=random.choices(
                    [Payment.STATUS_CLEARED, Payment.STATUS_PENDING, Payment.STATUS_FAILED],
                    weights=[8, 1, 1],
                )[0],
                reference_no=f"REF{1000 + i}",
                date=rand_date_within(-120, 30),
                notes="",
                created_by=random.choice(all_staff) if all_staff else None,
            )
        self.stdout.write(self.style.SUCCESS(f"✓ payments: +{n}"))

        # -------------------------------------------------------------------
        # 11. Packages + Gallery (if empty)
        # -------------------------------------------------------------------
        if not Package.objects.exists():
            self.stdout.write(self.style.WARNING("Run: python manage.py seed_packages"))
        if not GalleryImage.objects.exists():
            GalleryImage.objects.create(
                title="Grand Wedding · Udaipur",
                image_url="https://upload.wikimedia.org/wikipedia/commons/d/da/Taj-Mahal.jpg",
                category="wedding", sort_order=1,
            )
            self.stdout.write(self.style.SUCCESS("✓ 1 sample gallery image"))

        # -------------------------------------------------------------------
        # summary
        # -------------------------------------------------------------------
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== SEED COMPLETE ==="))
        self.stdout.write(f"  Staff:          {Staff.objects.count()}")
        self.stdout.write(f"  Customers:      {Customer.objects.count()}")
        self.stdout.write(f"  Enquiries:      {Enquiry.objects.count()}")
        self.stdout.write(f"  Bookings:       {Booking.objects.count()}")
        self.stdout.write(f"  Events:         {Event.objects.count()}")
        self.stdout.write(f"  Vendors:        {Vendor.objects.count()}")
        self.stdout.write(f"  Collaborations: {Collaboration.objects.count()}")
        self.stdout.write(f"  Tasks:          {Task.objects.count()}")
        self.stdout.write(f"  Expenses:       {Expense.objects.count()}")
        self.stdout.write(f"  Payments:       {Payment.objects.count()}")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("Admin login:  admin@bookmyshaadi.local / admin12345"))
        self.stdout.write(self.style.WARNING("Other staff:  staffN@bookmyshaadi.local / demo12345"))
        self.stdout.write(self.style.WARNING("Customers:    customerN@example.com / demo12345"))
