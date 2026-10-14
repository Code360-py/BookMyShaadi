"""
Staff backend views.
"""

from decimal import Decimal
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from django.forms import DateField, DecimalField, IntegerField
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.auth import (
    get_current_staff,
    login_staff,
    logout_staff,
    role_required,
    staff_required,
)
from accounts.flash import add_flash
from accounts.models import Customer, Staff
from audit.helpers import log as audit_log
from audit.models import AuditLog
from accounts.security import generate_temp_password
from bookings.models import Enquiry


# ===========================================================================
# Helpers
# ===========================================================================
def _parse_form_date(value):
    if not value:
        return None
    try:
        return DateField().clean(value)
    except ValidationError:
        return None


def _parse_form_integer(value, *, minimum=0):
    if value in (None, ""):
        return None
    try:
        return IntegerField(min_value=minimum).clean(value)
    except ValidationError:
        return None


def _parse_form_amount(value, *, allow_zero=False):
    if value in (None, ""):
        return None
    try:
        return DecimalField(
            max_digits=12,
            decimal_places=2,
            min_value=0 if allow_zero else Decimal("0.01"),
        ).clean(value)
    except ValidationError:
        return None


def _safe_next(request, default: str = "/staff/") -> str:
    nxt = request.GET.get("next") or request.POST.get("next") or ""
    if not nxt.startswith("/") or nxt.startswith("//") or "\\" in nxt:
        return default
    try:
        parts = urlsplit(nxt)
    except ValueError:
        return default
    if not parts.scheme and not parts.netloc:
        return nxt
    return default


# ===========================================================================
# Auth
# ===========================================================================
def staff_login(request):
    if get_current_staff(request) is not None:
        return redirect("staffpanel:dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        staff = Staff.objects.filter(email__iexact=email).first()
        if staff is None or not staff.is_active:
            audit_log(request, AuditLog.ACTION_LOGIN_FAILED, success=False,
                      detail=f"email={email}")
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "staffpanel/login.html",
                          {"email": email, "next": _safe_next(request)})

        if staff.is_locked():
            add_flash(request, "Account temporarily locked. Try again later.", "error")
            return render(request, "staffpanel/login.html",
                          {"email": email, "next": _safe_next(request)})

        if not staff.check_password(password):
            staff.register_failed_attempt(
                settings.LOGIN_MAX_ATTEMPTS,
                settings.LOGIN_LOCKOUT_MINUTES,
            )
            audit_log(request, AuditLog.ACTION_LOGIN_FAILED, staff=staff, success=False)
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "staffpanel/login.html",
                          {"email": email, "next": _safe_next(request)})

        staff.reset_failed_attempts()
        staff.last_login = timezone.now()
        staff.save(update_fields=["last_login"])

        login_staff(request, staff)
        audit_log(request, AuditLog.ACTION_LOGIN, staff=staff)
        add_flash(request, f"Welcome back, {staff.full_name}.", "success")

        if staff.must_change_password:
            return redirect("staffpanel:force_password_change")

        return redirect(_safe_next(request))

    return render(request, "staffpanel/login.html", {"next": _safe_next(request)})


@staff_required
def staff_logout(request):
    staff = get_current_staff(request)
    audit_log(request, AuditLog.ACTION_LOGOUT, staff=staff)
    logout_staff(request)
    return redirect("/login/?tab=staff")


@staff_required
def force_password_change(request):
    staff = get_current_staff(request)

    if request.method == "POST":
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""

        if len(p1) < 8:
            add_flash(request, "Password must be at least 8 characters.", "error")
        elif p1 != p2:
            add_flash(request, "Passwords do not match.", "error")
        else:
            staff.set_password(p1)
            staff.must_change_password = False
            staff.save(update_fields=["password", "must_change_password"])
            audit_log(request, AuditLog.ACTION_PASSWORD_CHANGE, staff=staff)
            add_flash(request, "Password updated.", "success")
            return redirect("staffpanel:dashboard")

    return render(request, "staffpanel/force_password_change.html", {"staff": staff})


# ===========================================================================
# Dashboard
# ===========================================================================
@staff_required
def dashboard(request):
    from django.utils import timezone as _tz
    from events.models import Event
    from finance.models import Expense, Payment
    from tasks.models import Task
    from vendors.models import Vendor, Collaboration
    from bookings.models import Booking

    staff = get_current_staff(request)

    # counts
    enquiry_new_count = Enquiry.objects.filter(status=Enquiry.STATUS_NEW).count()
    enquiry_total_count = Enquiry.objects.count()
    customer_count = Customer.objects.count()
    booking_upcoming_count = Booking.objects.filter(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        scheduled_at__gte=_tz.now(),
    ).count()
    event_upcoming_count = Event.objects.filter(
        status__in=[Event.STATUS_PLANNING, Event.STATUS_CONFIRMED, Event.STATUS_ONGOING],
    ).count()
    task_open_count = Task.objects.exclude(
        status__in=[Task.STATUS_COMPLETED, Task.STATUS_CANCELLED]
    ).count()
    vendor_count = Vendor.objects.filter(is_active=True).count()
    collab_count = Collaboration.objects.filter(is_active=True).count()

    # money
    expense_total = Expense.objects.aggregate(s=models.Sum("amount"))["s"] or 0
    payment_received_total = Payment.objects.filter(
        direction=Payment.DIRECTION_IN, status=Payment.STATUS_CLEARED
    ).aggregate(s=models.Sum("amount"))["s"] or 0
    payment_paid_total = Payment.objects.filter(
        direction=Payment.DIRECTION_OUT, status=Payment.STATUS_CLEARED
    ).aggregate(s=models.Sum("amount"))["s"] or 0

    # recent + upcoming lists
    my_open_tasks = Task.objects.exclude(
        status__in=[Task.STATUS_COMPLETED, Task.STATUS_CANCELLED]
    ).filter(assigned_to=staff).order_by("due_date")[:5]

    upcoming_bookings = Booking.objects.filter(
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        scheduled_at__gte=_tz.now(),
    ).order_by("scheduled_at")[:5]

    recent_enquiries = Enquiry.objects.filter(
        status=Enquiry.STATUS_NEW
    ).order_by("-created_at")[:5]

    context = {
        "staff": staff,
        "nav": "dashboard",
        "enquiry_new_count": enquiry_new_count,
        "enquiry_total_count": enquiry_total_count,
        "customer_count": customer_count,
        "booking_upcoming_count": booking_upcoming_count,
        "event_upcoming_count": event_upcoming_count,
        "task_open_count": task_open_count,
        "vendor_count": vendor_count,
        "collab_count": collab_count,
        "expense_total": expense_total,
        "payment_received_total": payment_received_total,
        "payment_paid_total": payment_paid_total,
        "my_open_tasks": my_open_tasks,
        "upcoming_bookings": upcoming_bookings,
        "recent_enquiries": recent_enquiries,
    }
    return render(request, "staffpanel/dashboard.html", context)


# ===========================================================================
# Enquiries inbox
# ===========================================================================
@staff_required
def enquiry_list(request):
    status = request.GET.get("status", "").upper()
    qs = Enquiry.objects.all()
    if status and status in dict(Enquiry.STATUS_CHOICES):
        qs = qs.filter(status=status)

    return render(request, "staffpanel/enquiries/list.html", {"nav": "enquiries",
        "enquiries": qs,
        "status": status,
        "status_choices": Enquiry.STATUS_CHOICES,
    })


@staff_required
def enquiry_detail(request, pk):
    enquiry = get_object_or_404(Enquiry, pk=pk)
    return render(request, "staffpanel/enquiries/detail.html", {"enquiry": enquiry, "nav": "enquiries"})


@staff_required
def enquiry_update_status(request, pk):
    """POST-only: change status."""
    if request.method != "POST":
        return redirect("staffpanel:enquiry_detail", pk=pk)

    enquiry = get_object_or_404(Enquiry, pk=pk)
    new_status = (request.POST.get("status") or "").upper()
    if new_status in dict(Enquiry.STATUS_CHOICES):
        enquiry.status = new_status
        enquiry.handled_by = get_current_staff(request)
        enquiry.save(update_fields=["status", "handled_by", "updated_at"])
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Enquiry", object_id=enquiry.pk, object_repr=enquiry.full_name, detail=f"status={new_status}")
        add_flash(request, "Status updated.", "success")
    return redirect("staffpanel:enquiry_detail", pk=pk)


@staff_required
def enquiry_convert(request, pk):
    """Convert an enquiry to a Customer (or link to existing one)."""
    enquiry = get_object_or_404(Enquiry, pk=pk)

    if enquiry.status == Enquiry.STATUS_CONVERTED and enquiry.converted_customer:
        add_flash(request, "Already converted.", "info")
        return redirect("staffpanel:enquiry_detail", pk=pk)

    if request.method != "POST":
        # Show confirmation page
        return render(request, "staffpanel/enquiries/convert.html",
                      {"enquiry": enquiry, "nav": "enquiries"})

    # If a customer already exists with this email, link instead of creating
    existing = Customer.objects.filter(email__iexact=enquiry.email).first()
    if existing:
        customer = existing
        add_flash(request, f"Linked to existing customer: {customer.full_name}", "info")
    else:
        temp_password = generate_temp_password()
        customer = Customer(
            email=enquiry.email,
            full_name=enquiry.full_name,
            phone=enquiry.phone,
        )
        customer.set_password(temp_password)
        customer.save()
        add_flash(
            request,
            f"Customer created. Temporary password: {temp_password} "
            "(share securely, they should change it).",
            "warning",
        )

    enquiry.status = Enquiry.STATUS_CONVERTED
    enquiry.converted_customer = customer
    enquiry.handled_by = get_current_staff(request)
    enquiry.save(update_fields=[
        "status", "converted_customer", "handled_by", "updated_at"
    ])

    audit_log(request, AuditLog.ACTION_CONVERT, model_name="Enquiry", object_id=enquiry.pk, object_repr=enquiry.full_name, detail=f"customer_id={customer.pk}")
    add_flash(request, "Enquiry converted.", "success")
    return redirect("staffpanel:enquiry_detail", pk=pk)


# ===========================================================================
# Customers
# ===========================================================================
@staff_required
def customer_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Customer.objects.all()
    if q:
        qs = qs.filter(
            models.Q(full_name__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(phone__icontains=q)
        )
    return render(request, "staffpanel/customers/list.html", {"customers": qs, "q": q, "nav": "customers"})


@staff_required
def customer_detail(request, pk):
    from events.models import Event
    from bookings.models import Booking
    customer = get_object_or_404(Customer, pk=pk)
    staff = get_current_staff(request)
    events = Event.objects.filter(customer=customer).order_by("-date")
    bookings = Booking.objects.filter(customer=customer).order_by("-scheduled_at")[:10]
    return render(request, "staffpanel/customers/detail.html", {
        "customer": customer, "staff": staff,
        "events": events, "bookings": bookings,
        "nav": "customers",
    })


@staff_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()

        errors = []
        if not full_name:
            errors.append("Name is required.")
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if Customer.objects.filter(email__iexact=email).exclude(pk=customer.pk).exists():
            errors.append("Another customer already uses that email.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/customers/edit.html",
                          {"customer": customer})

        customer.full_name = full_name
        customer.phone = phone
        customer.email = email
        customer.save(update_fields=["full_name", "phone", "email", "updated_at"])
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Customer", object_id=customer.pk, object_repr=customer.full_name)
        add_flash(request, "Customer updated.", "success")
        return redirect("staffpanel:customer_detail", pk=customer.pk)

    return render(request, "staffpanel/customers/edit.html", {"customer": customer, "nav": "customers"})


@role_required("ADMIN", "MANAGER")
def customer_reset_password(request, pk):
    """Admin/manager resets a customer's password to a temp value."""
    if request.method != "POST":
        return redirect("staffpanel:customer_detail", pk=pk)

    customer = get_object_or_404(Customer, pk=pk)
    temp = generate_temp_password()
    customer.set_password(temp)
    customer.save(update_fields=["password", "updated_at"])
    audit_log(request, AuditLog.ACTION_PASSWORD_RESET, model_name="Customer", object_id=customer.pk, object_repr=customer.full_name)
    add_flash(request, f"Temporary password for {customer.email}: {temp}", "warning")
    return redirect("staffpanel:customer_detail", pk=pk)


@role_required("ADMIN")
def customer_toggle_active(request, pk):
    """Admin only: activate/deactivate a customer."""
    if request.method != "POST":
        return redirect("staffpanel:customer_detail", pk=pk)

    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = not customer.is_active
    customer.save(update_fields=["is_active", "updated_at"])
    state = "activated" if customer.is_active else "deactivated"
    audit_log(request, AuditLog.ACTION_TOGGLE, model_name="Customer", object_id=customer.pk, object_repr=customer.full_name, detail=state)
    add_flash(request, f"Customer {state}.", "success")
    return redirect("staffpanel:customer_detail", pk=pk)


# ===========================================================================
# Bookings
# ===========================================================================
from bookings.models import Booking
from django.utils.dateparse import parse_datetime


def _parse_dt(s: str):
    """Accept 'YYYY-MM-DDTHH:MM' from <input type=datetime-local>."""
    if not s:
        return None
    dt = parse_datetime(s)
    if dt is None:
        # try with seconds
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


@staff_required
def booking_list(request):
    status = (request.GET.get("status") or "").upper()
    qs = Booking.objects.select_related("customer", "assigned_to")
    if status and status in dict(Booking.STATUS_CHOICES):
        qs = qs.filter(status=status)
    return render(request, "staffpanel/bookings/list.html", {"nav": "bookings",
        "bookings": qs,
        "status": status,
        "status_choices": Booking.STATUS_CHOICES,
    })


@staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "assigned_to", "created_by"),
        pk=pk,
    )
    staff = get_current_staff(request)
    return render(request, "staffpanel/bookings/detail.html",
                  {"booking": booking, "staff": staff, "nav": "bookings"})


@staff_required
def booking_create(request):
    customers = Customer.objects.filter(is_active=True).order_by("full_name")
    staff_list = Staff.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        booking_type = request.POST.get("booking_type") or Booking.TYPE_CONSULT
        scheduled_at = _parse_dt(request.POST.get("scheduled_at"))
        duration = request.POST.get("duration_minutes") or "60"
        location = (request.POST.get("location") or "").strip()
        notes = (request.POST.get("notes") or "").strip()
        status = request.POST.get("status") or Booking.STATUS_PENDING
        assigned_id = request.POST.get("assigned_to") or None

        errors = []
        customer = None
        if customer_id:
            customer = Customer.objects.filter(pk=customer_id).first()
        if customer is None:
            errors.append("Pick a customer.")
        if scheduled_at is None:
            errors.append("A valid date & time is required.")
        duration = _parse_form_integer(duration, minimum=1)
        if duration is None:
            errors.append("Duration must be a positive number.")
            duration = 60
        if booking_type not in dict(Booking.TYPE_CHOICES):
            errors.append("Choose a valid booking type.")
        if status not in dict(Booking.STATUS_CHOICES):
            errors.append("Choose a valid booking status.")
            status = Booking.STATUS_PENDING

        assigned = None
        if assigned_id:
            assigned = Staff.objects.filter(pk=assigned_id).first()

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/bookings/form.html", {
                "customers": customers,
                "staff_list": staff_list,
                "data": request.POST,
                "mode": "create",
            })

        b = Booking.objects.create(
            customer=customer,
            booking_type=booking_type,
            scheduled_at=scheduled_at,
            duration_minutes=duration,
            location=location,
            notes=notes,
            status=status,
            assigned_to=assigned,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Booking", object_id=b.pk, object_repr=str(b))
        add_flash(request, "Booking created.", "success")
        return redirect("staffpanel:booking_detail", pk=b.pk)

    return render(request, "staffpanel/bookings/form.html", {
        "customers": customers,
        "staff_list": staff_list,
        "mode": "create",
    })


@staff_required
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    customers = Customer.objects.filter(is_active=True).order_by("full_name")
    staff_list = Staff.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        scheduled_at = _parse_dt(request.POST.get("scheduled_at"))
        if scheduled_at is None:
            add_flash(request, "A valid date & time is required.", "error")
            return redirect("staffpanel:booking_edit", pk=pk)

        duration = _parse_form_integer(request.POST.get("duration_minutes") or "60", minimum=1)
        customer = Customer.objects.filter(pk=request.POST.get("customer") or booking.customer_id).first()
        booking_type = request.POST.get("booking_type") or booking.booking_type
        status = request.POST.get("status") or booking.status
        if duration is None or customer is None or booking_type not in dict(Booking.TYPE_CHOICES) or status not in dict(Booking.STATUS_CHOICES):
            add_flash(request, "Choose a valid customer, booking type, status, and positive duration.", "error")
            return render(request, "staffpanel/bookings/form.html", {
                "booking": booking, "customers": customers, "staff_list": staff_list,
                "data": request.POST, "mode": "edit", "nav": "bookings",
            })

        booking.customer = customer
        booking.booking_type = booking_type
        booking.scheduled_at = scheduled_at
        booking.duration_minutes = duration
        booking.location = (request.POST.get("location") or "").strip()
        booking.notes = (request.POST.get("notes") or "").strip()
        booking.status = status
        assigned_id = request.POST.get("assigned_to") or None
        booking.assigned_to = Staff.objects.filter(pk=assigned_id, is_active=True).first() if assigned_id else None
        booking.save()

        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Booking", object_id=booking.pk, object_repr=str(booking))
        add_flash(request, "Booking updated.", "success")
        return redirect("staffpanel:booking_detail", pk=booking.pk)

    return render(request, "staffpanel/bookings/form.html", {
        "booking": booking,
        "customers": customers,
        "staff_list": staff_list,
        "mode": "edit",
    })


# ===========================================================================
# Events
# ===========================================================================
from events.models import Event


@staff_required
def event_list(request):
    status = (request.GET.get("status") or "").upper()
    q = (request.GET.get("q") or "").strip()

    qs = Event.objects.select_related("customer")
    if status and status in dict(Event.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            models.Q(title__icontains=q) |
            models.Q(customer__full_name__icontains=q) |
            models.Q(location__icontains=q)
        )

    return render(request, "staffpanel/events/list.html", {"nav": "events",
        "events": qs,
        "status": status,
        "q": q,
        "status_choices": Event.STATUS_CHOICES,
    })


@staff_required
def event_detail(request, pk):
    from tasks.models import Task
    from finance.models import Expense, Payment
    event = get_object_or_404(
        Event.objects.select_related("customer", "created_by"),
        pk=pk,
    )
    staff = get_current_staff(request)

    tasks = event.tasks.select_related("assigned_to").all()
    expenses = event.expenses.select_related("vendor").all()
    payments = event.payments.select_related("vendor").all()

    total_expenses = sum(e.amount for e in expenses)
    total_received = sum(p.amount for p in payments if p.direction == "IN" and p.status == "CLEARED")
    total_paid = sum(p.amount for p in payments if p.direction == "OUT" and p.status == "CLEARED")
    open_tasks = [t for t in tasks if t.status not in ("COMPLETED", "CANCELLED")]

    return render(request, "staffpanel/events/detail.html", {
        "event": event,
        "staff": staff,
        "tasks": tasks,
        "expenses": expenses,
        "payments": payments,
        "total_expenses": total_expenses,
        "total_received": total_received,
        "total_paid": total_paid,
        "open_task_count": len(open_tasks),
        "nav": "events",
    })


@staff_required
def event_create(request):
    customers = Customer.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        event_type = request.POST.get("event_type") or Event.TYPE_WEDDING
        customer_id = request.POST.get("customer")
        bride_name = (request.POST.get("bride_name") or "").strip()
        groom_name = (request.POST.get("groom_name") or "").strip()
        date = request.POST.get("date")
        end_date = request.POST.get("end_date") or None
        location = (request.POST.get("location") or "").strip()
        guest_count = request.POST.get("guest_count") or None
        budget = request.POST.get("budget") or "0"
        status = request.POST.get("status") or Event.STATUS_PLANNING
        notes = (request.POST.get("notes") or "").strip()

        parsed_date = _parse_form_date(date)
        parsed_end_date = _parse_form_date(end_date)
        raw_guest_count = request.POST.get("guest_count")
        parsed_guest_count = _parse_form_integer(raw_guest_count, minimum=0)
        parsed_budget = _parse_form_amount(budget, allow_zero=True)

        errors = []
        if not title:
            errors.append("Title is required.")
        if not customer_id:
            errors.append("Customer is required.")
        if parsed_date is None:
            errors.append("Enter a valid event date.")
        if end_date and parsed_end_date is None:
            errors.append("Enter a valid end date.")
        if parsed_date and parsed_end_date and parsed_end_date < parsed_date:
            errors.append("End date cannot be before the event date.")
        if raw_guest_count and parsed_guest_count is None:
            errors.append("Guest count must be a whole number zero or greater.")
        if parsed_budget is None:
            errors.append("Budget must be a valid non-negative amount with up to two decimal places.")
        if not location:
            errors.append("Location is required.")
        if event_type not in dict(Event.TYPE_CHOICES):
            errors.append("Choose a valid event type.")
        if status not in dict(Event.STATUS_CHOICES):
            errors.append("Choose a valid event status.")

        customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
        if customer is None:
            errors.append("Pick a valid customer.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/events/form.html", {
                "customers": customers,
                "data": request.POST,
                "mode": "create",
            })

        e = Event.objects.create(
            title=title,
            event_type=event_type,
            customer=customer,
            bride_name=bride_name,
            groom_name=groom_name,
            date=parsed_date,
            end_date=parsed_end_date,
            location=location,
            guest_count=parsed_guest_count,
            budget=parsed_budget,
            status=status,
            notes=notes,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Event", object_id=e.pk, object_repr=e.title)
        add_flash(request, "Event created.", "success")
        return redirect("staffpanel:event_detail", pk=e.pk)

    return render(request, "staffpanel/events/form.html", {
        "customers": customers,
        "mode": "create",
    })


@staff_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    customers = Customer.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        title = (request.POST.get("title") or event.title).strip()
        event_type = request.POST.get("event_type") or event.event_type
        customer = Customer.objects.filter(pk=request.POST.get("customer") or event.customer_id).first()
        date_value = request.POST.get("date") or event.date
        end_date_value = request.POST.get("end_date") or None
        guest_count_value = request.POST.get("guest_count") or None
        budget_value = request.POST.get("budget") or event.budget
        status = request.POST.get("status") or event.status
        location = (request.POST.get("location") or "").strip()
        parsed_date = _parse_form_date(date_value)
        parsed_end_date = _parse_form_date(end_date_value)
        parsed_guest_count = _parse_form_integer(guest_count_value, minimum=0)
        parsed_budget = _parse_form_amount(budget_value, allow_zero=True)
        if (
            not title
            or customer is None
            or parsed_date is None
            or (end_date_value and parsed_end_date is None)
            or (parsed_date and parsed_end_date and parsed_end_date < parsed_date)
            or (guest_count_value and parsed_guest_count is None)
            or parsed_budget is None
            or not location
            or event_type not in dict(Event.TYPE_CHOICES)
            or status not in dict(Event.STATUS_CHOICES)
        ):
            add_flash(request, "Review the event details, dates, guest count, and budget.", "error")
            return render(request, "staffpanel/events/form.html", {
                "event": event, "customers": customers, "data": request.POST,
                "mode": "edit", "nav": "events",
            })

        event.title = title
        event.event_type = event_type
        event.customer = customer
        event.bride_name = (request.POST.get("bride_name") or "").strip()
        event.groom_name = (request.POST.get("groom_name") or "").strip()
        event.date = parsed_date
        event.end_date = parsed_end_date
        event.location = location
        event.guest_count = parsed_guest_count
        event.budget = parsed_budget
        event.status = status
        event.notes = (request.POST.get("notes") or "").strip()
        event.save()

        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Event", object_id=event.pk, object_repr=event.title)
        add_flash(request, "Event updated.", "success")
        return redirect("staffpanel:event_detail", pk=event.pk)

    return render(request, "staffpanel/events/form.html", {
        "event": event,
        "customers": customers,
        "mode": "edit",
    })


@role_required("ADMIN", "MANAGER")
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method != "POST":
        return redirect("staffpanel:event_detail", pk=pk)

    title = event.title
    event.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Event", object_repr=title)
    add_flash(request, f"Event '{title}' deleted.", "success")
    return redirect("staffpanel:event_list")


# ===========================================================================
# Vendors
# ===========================================================================
from vendors.models import Vendor, Collaboration


@staff_required
def vendor_list(request):
    q = (request.GET.get("q") or "").strip()
    service = (request.GET.get("service") or "").upper()
    qs = Vendor.objects.all()
    if q:
        qs = qs.filter(
            models.Q(name__icontains=q) |
            models.Q(contact_person__icontains=q) |
            models.Q(phone__icontains=q) |
            models.Q(email__icontains=q)
        )
    if service and service in dict(Vendor.SERVICE_CHOICES):
        qs = qs.filter(service_type=service)
    return render(request, "staffpanel/vendors/list.html", {
        "vendors": qs,
        "q": q,
        "service": service,
        "service_choices": Vendor.SERVICE_CHOICES,
        "nav": "vendors",
    })


@staff_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    staff = get_current_staff(request)
    return render(request, "staffpanel/vendors/detail.html",
                  {"vendor": vendor, "staff": staff, "nav": "vendors"})


@staff_required
def vendor_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        service_type = request.POST.get("service_type") or Vendor.SERVICE_OTHER
        contact_person = (request.POST.get("contact_person") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        address = (request.POST.get("address") or "").strip()
        website = (request.POST.get("website") or "").strip()
        notes = (request.POST.get("notes") or "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if service_type not in dict(Vendor.SERVICE_CHOICES):
            errors.append("Invalid service type.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/vendors/form.html", {
                "data": request.POST,
                "service_choices": Vendor.SERVICE_CHOICES,
                "mode": "create",
                "nav": "vendors",
            })

        v = Vendor.objects.create(
            name=name, service_type=service_type,
            contact_person=contact_person, phone=phone, email=email,
            address=address, website=website, notes=notes,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Vendor", object_id=v.pk, object_repr=v.name)
        add_flash(request, "Vendor created.", "success")
        return redirect("staffpanel:vendor_detail", pk=v.pk)

    return render(request, "staffpanel/vendors/form.html", {
        "service_choices": Vendor.SERVICE_CHOICES,
        "mode": "create",
        "nav": "vendors",
    })


@staff_required
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == "POST":
        vendor.name = (request.POST.get("name") or vendor.name).strip()
        st = request.POST.get("service_type") or vendor.service_type
        if st in dict(Vendor.SERVICE_CHOICES):
            vendor.service_type = st
        vendor.contact_person = (request.POST.get("contact_person") or "").strip()
        vendor.phone = (request.POST.get("phone") or "").strip()
        vendor.email = (request.POST.get("email") or "").strip()
        vendor.address = (request.POST.get("address") or "").strip()
        vendor.website = (request.POST.get("website") or "").strip()
        vendor.notes = (request.POST.get("notes") or "").strip()
        vendor.is_active = "is_active" in request.POST
        vendor.save()
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Vendor", object_id=vendor.pk, object_repr=vendor.name)
        add_flash(request, "Vendor updated.", "success")
        return redirect("staffpanel:vendor_detail", pk=vendor.pk)

    return render(request, "staffpanel/vendors/form.html", {
        "vendor": vendor,
        "service_choices": Vendor.SERVICE_CHOICES,
        "mode": "edit",
        "nav": "vendors",
    })


@role_required("ADMIN", "MANAGER")
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method != "POST":
        return redirect("staffpanel:vendor_detail", pk=pk)
    name = vendor.name
    vendor.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Vendor", object_repr=name)
    add_flash(request, f"Vendor '{name}' deleted.", "success")
    return redirect("staffpanel:vendor_list")


# ===========================================================================
# Collaborations
# ===========================================================================
@staff_required
def collab_list(request):
    q = (request.GET.get("q") or "").strip()
    ptype = (request.GET.get("type") or "").upper()
    qs = Collaboration.objects.all()
    if q:
        qs = qs.filter(
            models.Q(partner_name__icontains=q) |
            models.Q(contact_person__icontains=q) |
            models.Q(phone__icontains=q)
        )
    if ptype and ptype in dict(Collaboration.TYPE_CHOICES):
        qs = qs.filter(partner_type=ptype)
    return render(request, "staffpanel/collabs/list.html", {
        "collabs": qs,
        "q": q,
        "ptype": ptype,
        "type_choices": Collaboration.TYPE_CHOICES,
        "nav": "collabs",
    })


@staff_required
def collab_detail(request, pk):
    c = get_object_or_404(Collaboration, pk=pk)
    staff = get_current_staff(request)
    return render(request, "staffpanel/collabs/detail.html",
                  {"collab": c, "staff": staff, "nav": "collabs"})


@staff_required
def collab_create(request):
    if request.method == "POST":
        partner_name = (request.POST.get("partner_name") or "").strip()
        partner_type = request.POST.get("partner_type") or Collaboration.TYPE_OTHER

        errors = []
        if not partner_name:
            errors.append("Partner name is required.")
        if partner_type not in dict(Collaboration.TYPE_CHOICES):
            errors.append("Invalid partner type.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/collabs/form.html", {
                "data": request.POST,
                "type_choices": Collaboration.TYPE_CHOICES,
                "mode": "create",
                "nav": "collabs",
            })

        c = Collaboration.objects.create(
            partner_name=partner_name,
            partner_type=partner_type,
            contact_person=(request.POST.get("contact_person") or "").strip(),
            phone=(request.POST.get("phone") or "").strip(),
            email=(request.POST.get("email") or "").strip(),
            commission_pct=request.POST.get("commission_pct") or 0,
            notes=(request.POST.get("notes") or "").strip(),
            is_active="is_active" in request.POST,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Collaboration", object_id=c.pk, object_repr=c.partner_name)
        add_flash(request, "Collaboration created.", "success")
        return redirect("staffpanel:collab_detail", pk=c.pk)

    return render(request, "staffpanel/collabs/form.html", {
        "type_choices": Collaboration.TYPE_CHOICES,
        "mode": "create",
        "nav": "collabs",
    })


@staff_required
def collab_edit(request, pk):
    c = get_object_or_404(Collaboration, pk=pk)

    if request.method == "POST":
        c.partner_name = (request.POST.get("partner_name") or c.partner_name).strip()
        pt = request.POST.get("partner_type") or c.partner_type
        if pt in dict(Collaboration.TYPE_CHOICES):
            c.partner_type = pt
        c.contact_person = (request.POST.get("contact_person") or "").strip()
        c.phone = (request.POST.get("phone") or "").strip()
        c.email = (request.POST.get("email") or "").strip()
        c.commission_pct = request.POST.get("commission_pct") or 0
        c.notes = (request.POST.get("notes") or "").strip()
        c.is_active = "is_active" in request.POST
        c.save()
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Collaboration", object_id=c.pk, object_repr=c.partner_name)
        add_flash(request, "Collaboration updated.", "success")
        return redirect("staffpanel:collab_detail", pk=c.pk)

    return render(request, "staffpanel/collabs/form.html", {
        "collab": c,
        "type_choices": Collaboration.TYPE_CHOICES,
        "mode": "edit",
        "nav": "collabs",
    })


@role_required("ADMIN", "MANAGER")
def collab_delete(request, pk):
    c = get_object_or_404(Collaboration, pk=pk)
    if request.method != "POST":
        return redirect("staffpanel:collab_detail", pk=pk)
    name = c.partner_name
    c.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Collaboration", object_repr=name)
    add_flash(request, f"Collaboration '{name}' deleted.", "success")
    return redirect("staffpanel:collab_list")


# ===========================================================================
# Tasks
# ===========================================================================
from tasks.models import Task


@staff_required
def task_list(request):
    status = (request.GET.get("status") or "").upper()
    q = (request.GET.get("q") or "").strip()
    mine = request.GET.get("mine") == "1"

    qs = Task.objects.select_related("event", "assigned_to")
    if status and status in dict(Task.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if mine:
        qs = qs.filter(assigned_to=get_current_staff(request))
    if q:
        qs = qs.filter(
            models.Q(title__icontains=q) |
            models.Q(event__title__icontains=q) |
            models.Q(assigned_to__full_name__icontains=q)
        )

    return render(request, "staffpanel/tasks/list.html", {
        "tasks": qs,
        "status": status,
        "q": q,
        "mine": mine,
        "status_choices": Task.STATUS_CHOICES,
        "nav": "tasks",
    })


@staff_required
def task_detail(request, pk):
    task = get_object_or_404(
        Task.objects.select_related("event", "assigned_to", "created_by"),
        pk=pk,
    )
    staff = get_current_staff(request)
    return render(request, "staffpanel/tasks/detail.html",
                  {"task": task, "staff": staff, "nav": "tasks"})


@staff_required
def task_create(request):
    from events.models import Event
    events = Event.objects.order_by("-date")
    staff_list = Staff.objects.filter(is_active=True).order_by("full_name")
    preselect_event = request.GET.get("event")

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        event_id = request.POST.get("event")
        description = (request.POST.get("description") or "").strip()
        assigned_id = request.POST.get("assigned_to") or None
        due_date = request.POST.get("due_date") or None
        parsed_due_date = _parse_form_date(due_date)
        priority = request.POST.get("priority") or Task.PRIORITY_MED
        status = request.POST.get("status") or Task.STATUS_PENDING

        errors = []
        if not title:
            errors.append("Title is required.")
        event = Event.objects.filter(pk=event_id).first() if event_id else None
        if event is None:
            errors.append("Pick an event.")
        if due_date and parsed_due_date is None:
            errors.append("Enter a valid due date.")
        if priority not in dict(Task.PRIORITY_CHOICES):
            errors.append("Choose a valid priority.")
        if status not in dict(Task.STATUS_CHOICES):
            errors.append("Choose a valid task status.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/tasks/form.html", {
                "events": events, "staff_list": staff_list,
                "data": request.POST, "mode": "create", "nav": "tasks",
            })

        assigned = Staff.objects.filter(pk=assigned_id).first() if assigned_id else None
        t = Task.objects.create(
            title=title, description=description,
            event=event, assigned_to=assigned,
            due_date=parsed_due_date, priority=priority, status=status,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Task", object_id=t.pk, object_repr=t.title)
        add_flash(request, "Task created.", "success")
        return redirect("staffpanel:task_detail", pk=t.pk)

    return render(request, "staffpanel/tasks/form.html", {
        "events": events, "staff_list": staff_list,
        "preselect_event": preselect_event,
        "mode": "create", "nav": "tasks",
    })


@staff_required
def task_edit(request, pk):
    from events.models import Event
    task = get_object_or_404(Task, pk=pk)
    events = Event.objects.order_by("-date")
    staff_list = Staff.objects.filter(is_active=True).order_by("full_name")

    if request.method == "POST":
        task.title = (request.POST.get("title") or task.title).strip()
        task.description = (request.POST.get("description") or "").strip()
        event_id = request.POST.get("event")
        if event_id:
            e = Event.objects.filter(pk=event_id).first()
            if e:
                task.event = e
        assigned_id = request.POST.get("assigned_to") or None
        task.assigned_to_id = assigned_id if assigned_id else None
        due_date = request.POST.get("due_date") or None
        parsed_due_date = _parse_form_date(due_date)
        priority = request.POST.get("priority") or task.priority
        status = request.POST.get("status") or task.status
        if (
            (due_date and parsed_due_date is None)
            or priority not in dict(Task.PRIORITY_CHOICES)
            or status not in dict(Task.STATUS_CHOICES)
        ):
            add_flash(request, "Enter a valid due date, priority, and task status.", "error")
            return render(request, "staffpanel/tasks/form.html", {
                "task": task, "events": events, "staff_list": staff_list,
                "data": request.POST, "mode": "edit", "nav": "tasks",
            })
        task.due_date = parsed_due_date
        task.priority = priority
        task.status = status
        task.save()
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Task", object_id=task.pk, object_repr=task.title)
        add_flash(request, "Task updated.", "success")
        return redirect("staffpanel:task_detail", pk=task.pk)

    return render(request, "staffpanel/tasks/form.html", {
        "task": task, "events": events, "staff_list": staff_list,
        "mode": "edit", "nav": "tasks",
    })


@staff_required
def task_toggle_status(request, pk):
    """Quick toggle: PENDING ↔ COMPLETED."""
    if request.method != "POST":
        return redirect("staffpanel:task_detail", pk=pk)
    task = get_object_or_404(Task, pk=pk)
    if task.status == Task.STATUS_COMPLETED:
        task.status = Task.STATUS_PENDING
    else:
        task.status = Task.STATUS_COMPLETED
    task.save(update_fields=["status", "updated_at"])
    audit_log(request, AuditLog.ACTION_TOGGLE, model_name="Task", object_id=task.pk, object_repr=task.title, detail=task.status)
    add_flash(request, f"Task marked {task.get_status_display()}.", "success")
    return redirect(request.META.get("HTTP_REFERER") or "staffpanel:task_list")


@role_required("ADMIN", "MANAGER")
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method != "POST":
        return redirect("staffpanel:task_detail", pk=pk)
    title = task.title
    task.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Task", object_repr=title)
    add_flash(request, f"Task '{title}' deleted.", "success")
    return redirect("staffpanel:task_list")


# ===========================================================================
# Expenses
# ===========================================================================
from finance.models import Expense


@staff_required
def expense_list(request):
    status = (request.GET.get("status") or "").upper()
    q = (request.GET.get("q") or "").strip()
    event_id = request.GET.get("event") or None

    qs = Expense.objects.select_related("event", "vendor")
    if status and status in dict(Expense.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if event_id:
        qs = qs.filter(event_id=event_id)
    if q:
        qs = qs.filter(
            models.Q(description__icontains=q) |
            models.Q(event__title__icontains=q) |
            models.Q(vendor__name__icontains=q)
        )

    total = sum(e.amount for e in qs) if qs else 0

    return render(request, "staffpanel/expenses/list.html", {
        "expenses": qs,
        "status": status,
        "q": q,
        "event_id": event_id,
        "total": total,
        "status_choices": Expense.STATUS_CHOICES,
        "nav": "expenses",
    })


@staff_required
def expense_detail(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related("event", "vendor", "created_by"),
        pk=pk,
    )
    staff = get_current_staff(request)
    return render(request, "staffpanel/expenses/detail.html",
                  {"expense": expense, "staff": staff, "nav": "expenses"})


@staff_required
def expense_create(request):
    from events.models import Event
    events = Event.objects.order_by("-date")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")
    preselect_event = request.GET.get("event")

    if request.method == "POST":
        event_id = request.POST.get("event")
        vendor_id = request.POST.get("vendor") or None
        category = request.POST.get("category") or Expense.CAT_MISC
        description = (request.POST.get("description") or "").strip()
        amount = request.POST.get("amount") or "0"
        status = request.POST.get("status") or Expense.STATUS_PENDING
        date = request.POST.get("date")
        notes = (request.POST.get("notes") or "").strip()

        errors = []
        event = Event.objects.filter(pk=event_id).first() if event_id else None
        if event is None:
            errors.append("Pick an event.")
        parsed_date = _parse_form_date(date)
        if parsed_date is None:
            errors.append("Enter a valid date.")
        amt = _parse_form_amount(amount)
        if amt is None:
            errors.append("Amount must be a positive amount with up to two decimal places.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/expenses/form.html", {
                "events": events, "vendors": vendors,
                "data": request.POST, "mode": "create", "nav": "expenses",
            })

        vendor = Vendor.objects.filter(pk=vendor_id).first() if vendor_id else None
        ex = Expense.objects.create(
            event=event, vendor=vendor,
            category=category, description=description,
            amount=amt, status=status, date=parsed_date, notes=notes,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Expense", object_id=ex.pk, object_repr=str(ex))
        add_flash(request, "Expense recorded.", "success")
        return redirect("staffpanel:expense_detail", pk=ex.pk)

    return render(request, "staffpanel/expenses/form.html", {
        "events": events, "vendors": vendors,
        "preselect_event": preselect_event,
        "mode": "create", "nav": "expenses",
    })


@staff_required
def expense_edit(request, pk):
    from events.models import Event
    expense = get_object_or_404(Expense, pk=pk)
    events = Event.objects.order_by("-date")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        event_id = request.POST.get("event")
        if event_id:
            e = Event.objects.filter(pk=event_id).first()
            if e:
                expense.event = e
        vendor_id = request.POST.get("vendor") or None
        expense.vendor_id = vendor_id if vendor_id else None
        category = request.POST.get("category") or expense.category
        status = request.POST.get("status") or expense.status
        expense.description = (request.POST.get("description") or "").strip()
        amount = request.POST.get("amount") or expense.amount
        date_value = request.POST.get("date") or expense.date
        parsed_amount = _parse_form_amount(amount)
        parsed_date = _parse_form_date(date_value)
        if parsed_amount is None or parsed_date is None or category not in dict(Expense.CATEGORY_CHOICES) or status not in dict(Expense.STATUS_CHOICES):
            add_flash(request, "Enter a valid positive amount, date, category, and status.", "error")
            return render(request, "staffpanel/expenses/form.html", {
                "expense": expense, "events": events, "vendors": vendors,
                "data": request.POST, "mode": "edit", "nav": "expenses",
            })
        expense.amount = parsed_amount
        expense.category = category
        expense.status = status
        expense.date = parsed_date
        expense.notes = (request.POST.get("notes") or "").strip()
        expense.save()
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Expense", object_id=expense.pk, object_repr=str(expense))
        add_flash(request, "Expense updated.", "success")
        return redirect("staffpanel:expense_detail", pk=expense.pk)

    return render(request, "staffpanel/expenses/form.html", {
        "expense": expense, "events": events, "vendors": vendors,
        "mode": "edit", "nav": "expenses",
    })


@role_required("ADMIN", "MANAGER")
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method != "POST":
        return redirect("staffpanel:expense_detail", pk=pk)
    expense.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Expense", object_repr=str(expense))
    add_flash(request, "Expense deleted.", "success")
    return redirect("staffpanel:expense_list")


# ===========================================================================
# Payments
# ===========================================================================
from finance.models import Payment


@staff_required
def payment_list(request):
    status = (request.GET.get("status") or "").upper()
    direction = (request.GET.get("direction") or "").upper()
    q = (request.GET.get("q") or "").strip()

    qs = Payment.objects.select_related("event", "vendor")
    if status and status in dict(Payment.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if direction and direction in dict(Payment.DIRECTION_CHOICES):
        qs = qs.filter(direction=direction)
    if q:
        qs = qs.filter(
            models.Q(reference_no__icontains=q) |
            models.Q(event__title__icontains=q) |
            models.Q(vendor__name__icontains=q)
        )

    received = sum(p.amount for p in qs if p.direction == Payment.DIRECTION_IN and p.status == Payment.STATUS_CLEARED)
    paid = sum(p.amount for p in qs if p.direction == Payment.DIRECTION_OUT and p.status == Payment.STATUS_CLEARED)

    return render(request, "staffpanel/payments/list.html", {
        "payments": qs,
        "status": status,
        "direction": direction,
        "q": q,
        "received": received,
        "paid": paid,
        "status_choices": Payment.STATUS_CHOICES,
        "direction_choices": Payment.DIRECTION_CHOICES,
        "nav": "payments",
    })


@staff_required
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related("event", "vendor", "created_by"),
        pk=pk,
    )
    staff = get_current_staff(request)
    return render(request, "staffpanel/payments/detail.html",
                  {"payment": payment, "staff": staff, "nav": "payments"})


@staff_required
def payment_create(request):
    from events.models import Event
    events = Event.objects.order_by("-date")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")
    preselect_event = request.GET.get("event")
    preselect_direction = request.GET.get("direction") or Payment.DIRECTION_IN

    if request.method == "POST":
        event_id = request.POST.get("event")
        vendor_id = request.POST.get("vendor") or None
        direction = request.POST.get("direction") or Payment.DIRECTION_IN
        amount = request.POST.get("amount") or "0"
        method = request.POST.get("method") or Payment.METHOD_CASH
        status = request.POST.get("status") or Payment.STATUS_CLEARED
        reference_no = (request.POST.get("reference_no") or "").strip()
        date = request.POST.get("date")
        notes = (request.POST.get("notes") or "").strip()

        errors = []
        event = Event.objects.filter(pk=event_id).first() if event_id else None
        if event is None:
            errors.append("Pick an event.")
        parsed_date = _parse_form_date(date)
        if parsed_date is None:
            errors.append("Enter a valid date.")
        amt = _parse_form_amount(amount)
        if amt is None:
            errors.append("Amount must be a positive amount with up to two decimal places.")
        if direction == Payment.DIRECTION_OUT and not vendor_id:
            errors.append("Outgoing payments require a vendor.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/payments/form.html", {
                "events": events, "vendors": vendors,
                "data": request.POST, "mode": "create", "nav": "payments",
            })

        vendor = Vendor.objects.filter(pk=vendor_id).first() if vendor_id else None
        p = Payment.objects.create(
            event=event, vendor=vendor,
            direction=direction, amount=amt,
            method=method, status=status,
            reference_no=reference_no, date=parsed_date, notes=notes,
            created_by=get_current_staff(request),
        )
        audit_log(request, AuditLog.ACTION_CREATE, model_name="Payment", object_id=p.pk, object_repr=str(p))
        add_flash(request, "Payment recorded.", "success")
        return redirect("staffpanel:payment_detail", pk=p.pk)

    return render(request, "staffpanel/payments/form.html", {
        "events": events, "vendors": vendors,
        "preselect_event": preselect_event,
        "preselect_direction": preselect_direction,
        "mode": "create", "nav": "payments",
    })


@staff_required
def payment_edit(request, pk):
    from events.models import Event
    payment = get_object_or_404(Payment, pk=pk)
    events = Event.objects.order_by("-date")
    vendors = Vendor.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        event_id = request.POST.get("event")
        if event_id:
            e = Event.objects.filter(pk=event_id).first()
            if e:
                payment.event = e
        vendor_id = request.POST.get("vendor") or None
        payment.vendor_id = vendor_id if vendor_id else None
        direction = request.POST.get("direction") or payment.direction
        method = request.POST.get("method") or payment.method
        status = request.POST.get("status") or payment.status
        amount = request.POST.get("amount") or payment.amount
        date_value = request.POST.get("date") or payment.date
        parsed_amount = _parse_form_amount(amount)
        parsed_date = _parse_form_date(date_value)
        if (
            parsed_amount is None
            or parsed_date is None
            or direction not in dict(Payment.DIRECTION_CHOICES)
            or method not in dict(Payment.METHOD_CHOICES)
            or status not in dict(Payment.STATUS_CHOICES)
        ):
            add_flash(request, "Enter a valid positive amount, date, direction, method, and status.", "error")
            return render(request, "staffpanel/payments/form.html", {
                "payment": payment, "events": events, "vendors": vendors,
                "data": request.POST, "mode": "edit", "nav": "payments",
            })
        payment.amount = parsed_amount
        payment.direction = direction
        payment.method = method
        payment.status = status
        payment.reference_no = (request.POST.get("reference_no") or "").strip()
        payment.date = parsed_date
        payment.notes = (request.POST.get("notes") or "").strip()
        payment.save()
        audit_log(request, AuditLog.ACTION_UPDATE, model_name="Payment", object_id=payment.pk, object_repr=str(payment))
        add_flash(request, "Payment updated.", "success")
        return redirect("staffpanel:payment_detail", pk=payment.pk)

    return render(request, "staffpanel/payments/form.html", {
        "payment": payment, "events": events, "vendors": vendors,
        "mode": "edit", "nav": "payments",
    })


@role_required("ADMIN", "MANAGER")
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method != "POST":
        return redirect("staffpanel:payment_detail", pk=pk)
    payment.delete()
    audit_log(request, AuditLog.ACTION_DELETE, model_name="Payment", object_repr=str(payment))
    add_flash(request, "Payment deleted.", "success")
    return redirect("staffpanel:payment_list")


# ===========================================================================
# Audit log
# ===========================================================================
@role_required("ADMIN", "MANAGER")
def audit_list(request):
    action = (request.GET.get("action") or "").upper()
    q = (request.GET.get("q") or "").strip()

    qs = AuditLog.objects.select_related("actor")
    if action and action in dict(AuditLog.ACTION_CHOICES):
        qs = qs.filter(action=action)
    if q:
        qs = qs.filter(
            models.Q(actor_email__icontains=q) |
            models.Q(model_name__icontains=q) |
            models.Q(object_repr__icontains=q) |
            models.Q(detail__icontains=q)
        )

    # limit to 500 recent entries for performance
    qs = qs[:500]

    return render(request, "staffpanel/audit/list.html", {
        "entries": qs,
        "action": action,
        "q": q,
        "action_choices": AuditLog.ACTION_CHOICES,
        "nav": "audit",
    })


@role_required("ADMIN", "MANAGER")
def audit_detail(request, pk):
    entry = get_object_or_404(AuditLog.objects.select_related("actor"), pk=pk)
    return render(request, "staffpanel/audit/detail.html",
                  {"entry": entry, "nav": "audit"})


# ===========================================================================
# Staff management (ADMIN only)
# ===========================================================================
@role_required("ADMIN")
def staff_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Staff.objects.all().order_by("role", "full_name")
    if q:
        qs = qs.filter(
            models.Q(full_name__icontains=q) |
            models.Q(email__icontains=q) |
            models.Q(phone__icontains=q)
        )
    return render(request, "staffpanel/staff/list.html", {
        "staff_list": qs,
        "q": q,
        "nav": "staff",
    })


@role_required("ADMIN")
def staff_detail(request, pk):
    member = get_object_or_404(Staff, pk=pk)
    me = get_current_staff(request)
    return render(request, "staffpanel/staff/detail.html", {
        "member": member,
        "me": me,
        "nav": "staff",
    })


@role_required("ADMIN")
def staff_create(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        phone = (request.POST.get("phone") or "").strip()
        role = request.POST.get("role") or Staff.ROLE_STAFF
        password = request.POST.get("password") or ""

        errors = []
        if not full_name or len(full_name) > 255:
            errors.append("Enter a name with 1 to 255 characters.")
        try:
            EmailValidator()(email)
        except ValidationError:
            errors.append("Enter a valid email address.")
        if Staff.objects.filter(email__iexact=email).exists():
            errors.append("A staff member with that email already exists.")
        if len(phone) > 20:
            errors.append("Phone number must be 20 characters or fewer.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if role not in dict(Staff.ROLE_CHOICES):
            errors.append("Invalid role.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/staff/form.html", {
                "data": request.POST, "mode": "create",
                "role_choices": Staff.ROLE_CHOICES,
                "nav": "staff",
            })

        member = Staff(
            full_name=full_name, email=email, phone=phone,
            role=role, is_active=True,
        )
        member.set_password(password)
        member.save()

        audit_log(
            request, AuditLog.ACTION_CREATE,
            model_name="Staff", object_id=member.pk, object_repr=member.full_name,
            detail=f"role={role}",
        )
        add_flash(request, f"Staff '{member.full_name}' created.", "success")
        return redirect("staffpanel:staff_detail", pk=member.pk)

    return render(request, "staffpanel/staff/form.html", {
        "mode": "create",
        "role_choices": Staff.ROLE_CHOICES,
        "nav": "staff",
    })


@role_required("ADMIN")
def staff_edit(request, pk):
    member = get_object_or_404(Staff, pk=pk)
    me = get_current_staff(request)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        role = request.POST.get("role") or member.role

        errors = []
        if not full_name or len(full_name) > 255:
            errors.append("Enter a name with 1 to 255 characters.")
        if len(phone) > 20:
            errors.append("Phone number must be 20 characters or fewer.")
        if role not in dict(Staff.ROLE_CHOICES):
            errors.append("Invalid role.")
        # Prevent self-demotion from last admin
        if member.pk == me.pk and role != Staff.ROLE_ADMIN:
            if Staff.objects.filter(role=Staff.ROLE_ADMIN, is_active=True).count() <= 1:
                errors.append("You're the only admin — cannot demote yourself.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "staffpanel/staff/form.html", {
                "member": member, "mode": "edit",
                "role_choices": Staff.ROLE_CHOICES,
                "nav": "staff",
            })

        old_role = member.role
        member.full_name = full_name
        member.phone = phone
        member.role = role
        member.save(update_fields=["full_name", "phone", "role", "updated_at"])

        audit_log(
            request, AuditLog.ACTION_UPDATE,
            model_name="Staff", object_id=member.pk, object_repr=member.full_name,
            detail=f"role {old_role} → {role}",
        )
        add_flash(request, "Staff updated.", "success")
        return redirect("staffpanel:staff_detail", pk=member.pk)

    return render(request, "staffpanel/staff/form.html", {
        "member": member, "mode": "edit",
        "role_choices": Staff.ROLE_CHOICES,
        "nav": "staff",
    })


@role_required("ADMIN")
def staff_reset_password(request, pk):
    if request.method != "POST":
        return redirect("staffpanel:staff_detail", pk=pk)

    member = get_object_or_404(Staff, pk=pk)
    temp = member.reset_password_to_temp()

    audit_log(
        request, AuditLog.ACTION_PASSWORD_RESET,
        model_name="Staff", object_id=member.pk, object_repr=member.full_name,
    )
    add_flash(request,
              f"Temporary password for {member.email}: {temp} "
              "(share securely — they must change it on next login).",
              "warning")
    return redirect("staffpanel:staff_detail", pk=pk)


@role_required("ADMIN")
def staff_toggle_active(request, pk):
    if request.method != "POST":
        return redirect("staffpanel:staff_detail", pk=pk)

    member = get_object_or_404(Staff, pk=pk)
    me = get_current_staff(request)

    if member.pk == me.pk:
        add_flash(request, "You cannot deactivate yourself.", "error")
        return redirect("staffpanel:staff_detail", pk=pk)

    # Prevent disabling the last admin
    if member.role == Staff.ROLE_ADMIN and member.is_active:
        remaining = Staff.objects.filter(
            role=Staff.ROLE_ADMIN, is_active=True,
        ).exclude(pk=member.pk).count()
        if remaining == 0:
            add_flash(request, "Cannot deactivate the last active admin.", "error")
            return redirect("staffpanel:staff_detail", pk=pk)

    member.is_active = not member.is_active
    member.save(update_fields=["is_active", "updated_at"])

    state = "activated" if member.is_active else "deactivated"
    audit_log(
        request, AuditLog.ACTION_TOGGLE,
        model_name="Staff", object_id=member.pk, object_repr=member.full_name,
        detail=state,
    )
    add_flash(request, f"Staff {state}.", "success")
    return redirect("staffpanel:staff_detail", pk=member.pk)
