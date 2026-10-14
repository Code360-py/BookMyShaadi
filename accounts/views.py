"""Customer-side views: register, login, logout, dashboard, my bookings/events."""

from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.shortcuts import get_object_or_404, redirect, render

from .auth import (
    customer_required,
    get_current_customer,
    login_customer,
    logout_customer,
)
from .flash import add_flash
from .models import Customer


def _safe_next(request, default: str = "/account/") -> str:
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


def register(request):
    if get_current_customer(request) is not None:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""

        errors = []
        try:
            EmailValidator()(email)
        except ValidationError:
            errors.append("A valid email is required.")
        if not full_name or len(full_name) > 255:
            errors.append("Enter a name with 1 to 255 characters.")
        if len(phone) > 20:
            errors.append("Phone number must be 20 characters or fewer.")
        if len(p1) < 8:
            errors.append("Password must be at least 8 characters.")
        if p1 != p2:
            errors.append("Passwords do not match.")
        if Customer.objects.filter(email__iexact=email).exists():
            errors.append("An account with that email already exists.")

        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "accounts/register.html", {
                "email": email, "full_name": full_name, "phone": phone,
            })

        c = Customer(email=email, full_name=full_name, phone=phone)
        c.set_password(p1)
        c.save()
        login_customer(request, c)
        add_flash(request, "Welcome to BookMyShaadi!", "success")
        return redirect(_safe_next(request))

    return render(request, "accounts/register.html", {})


def login_view(request):
    if get_current_customer(request) is not None:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        c = Customer.objects.filter(email__iexact=email).first()
        if c is None or not c.is_active:
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "accounts/login.html", {"email": email})

        if c.is_locked():
            add_flash(request, "Account temporarily locked. Try again later.", "error")
            return render(request, "accounts/login.html", {"email": email})

        if not c.check_password(password):
            from django.conf import settings
            c.register_failed_attempt(settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_LOCKOUT_MINUTES)
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "accounts/login.html", {"email": email})

        c.reset_failed_attempts()
        from django.utils import timezone
        c.last_login = timezone.now()
        c.save(update_fields=["last_login"])

        login_customer(request, c)
        add_flash(request, f"Welcome back, {c.full_name}.", "success")
        return redirect(_safe_next(request))

    return render(request, "accounts/login.html", {"next": _safe_next(request)})


@customer_required
def logout_view(request):
    logout_customer(request)
    add_flash(request, "You are signed out.", "info")
    return redirect("core:home")


@customer_required
def dashboard(request):
    from bookings.models import Booking
    from events.models import Event
    customer = get_current_customer(request)
    events = Event.objects.filter(customer=customer).order_by("-date")
    bookings = Booking.objects.filter(customer=customer).order_by("-scheduled_at")[:5]

    payments_in = []
    for ev in events:
        for p in ev.payments.filter(direction="IN", status="CLEARED"):
            payments_in.append(p)

    return render(request, "accounts/dashboard.html", {"nav": "dashboard",
        "customer": customer,
        "events": events,
        "bookings": bookings,
        "payments": payments_in,
    })


@customer_required
def my_events(request):
    from events.models import Event
    customer = get_current_customer(request)
    events = Event.objects.filter(customer=customer).order_by("-date")
    return render(request, "accounts/events.html", {"events": events, "nav": "events"})


@customer_required
def my_event_detail(request, pk):
    from events.models import Event
    customer = get_current_customer(request)
    event = get_object_or_404(Event, pk=pk, customer=customer)

    payments = event.payments.filter(direction="IN").order_by("-date")
    return render(request, "accounts/event_detail.html", {
        "event": event,
        "payments": payments,
        "nav": "events",
    })


@customer_required
def my_bookings(request):
    from bookings.models import Booking
    customer = get_current_customer(request)
    bookings = Booking.objects.filter(customer=customer).order_by("-scheduled_at")
    return render(request, "accounts/bookings.html", {"bookings": bookings, "nav": "bookings"})


@customer_required
def profile(request):
    customer = get_current_customer(request)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        if not full_name or len(full_name) > 255:
            add_flash(request, "Enter a name with 1 to 255 characters.", "error")
        elif len(phone) > 20:
            add_flash(request, "Phone number must be 20 characters or fewer.", "error")
        else:
            customer.full_name = full_name
            customer.phone = phone
            customer.save(update_fields=["full_name", "phone", "updated_at"])
            add_flash(request, "Profile updated.", "success")
            return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"customer": customer, "nav": "profile"})


@customer_required
def change_password(request):
    customer = get_current_customer(request)

    if request.method == "POST":
        old = request.POST.get("old_password") or ""
        p1 = request.POST.get("new_password1") or ""
        p2 = request.POST.get("new_password2") or ""

        if not customer.check_password(old):
            add_flash(request, "Current password is incorrect.", "error")
        elif len(p1) < 8:
            add_flash(request, "New password must be at least 8 characters.", "error")
        elif p1 != p2:
            add_flash(request, "New passwords do not match.", "error")
        else:
            customer.set_password(p1)
            customer.save(update_fields=["password", "updated_at"])
            add_flash(request, "Password changed.", "success")
            return redirect("accounts:dashboard")

    return render(request, "accounts/change_password.html", {"customer": customer, "nav": "password"})
