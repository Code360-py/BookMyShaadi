"""
Unified login/logout for customers and staff.
Single URL: /login/ with a tab switch for role.
"""

from django.conf import settings
from django.shortcuts import redirect, render
from django.utils import timezone
from urllib.parse import urlsplit

from .auth import (
    get_current_customer,
    get_current_staff,
    login_customer,
    login_staff,
    logout_customer,
    logout_staff,
)
from .flash import add_flash
from .models import Customer, Staff


def _safe_next(request, default: str) -> str:
    nxt = request.GET.get("next") or request.POST.get("next") or ""
    parts = urlsplit(nxt)
    if (
        nxt.startswith("/")
        and not nxt.startswith("//")
        and not parts.scheme
        and not parts.netloc
        and "\\" not in nxt
    ):
        return nxt
    return default


def unified_login(request):
    """One page, two tabs. `tab` = 'customer' | 'staff'."""
    # Already logged in?
    if get_current_staff(request) is not None:
        return redirect("staffpanel:dashboard")
    if get_current_customer(request) is not None:
        return redirect("accounts:dashboard")

    tab = (request.GET.get("tab") or request.POST.get("tab") or "customer").lower()
    if tab not in ("customer", "staff"):
        tab = "customer"

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if tab == "staff":
            default_next = "/staff/"
            staff = Staff.objects.filter(email__iexact=email).first()
            if staff is None or not staff.is_active:
                add_flash(request, "Invalid credentials.", "error")
                return render(request, "accounts/unified_login.html",
                              {"tab": "staff", "email": email,
                               "next": _safe_next(request, default_next)})

            if staff.is_locked():
                add_flash(request, "Account temporarily locked. Try again later.", "error")
                return render(request, "accounts/unified_login.html",
                              {"tab": "staff", "email": email,
                               "next": _safe_next(request, default_next)})

            if not staff.check_password(password):
                staff.register_failed_attempt(
                    settings.LOGIN_MAX_ATTEMPTS,
                    settings.LOGIN_LOCKOUT_MINUTES,
                )
                add_flash(request, "Invalid credentials.", "error")
                return render(request, "accounts/unified_login.html",
                              {"tab": "staff", "email": email,
                               "next": _safe_next(request, default_next)})

            staff.reset_failed_attempts()
            staff.last_login = timezone.now()
            staff.save(update_fields=["last_login"])
            login_staff(request, staff)

            try:
                from audit.helpers import log as audit_log
                from audit.models import AuditLog
                audit_log(request, AuditLog.ACTION_LOGIN, staff=staff)
            except Exception:
                pass

            add_flash(request, f"Welcome back, {staff.full_name}.", "success")
            if staff.must_change_password:
                return redirect("staffpanel:force_password_change")
            return redirect(_safe_next(request, default_next))

        # tab == customer
        default_next = "/account/"
        customer = Customer.objects.filter(email__iexact=email).first()
        if customer is None or not customer.is_active:
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "accounts/unified_login.html",
                          {"tab": "customer", "email": email,
                           "next": _safe_next(request, default_next)})

        if customer.is_locked():
            add_flash(request, "Account temporarily locked. Try again later.", "error")
            return render(request, "accounts/unified_login.html",
                          {"tab": "customer", "email": email,
                           "next": _safe_next(request, default_next)})

        if not customer.check_password(password):
            customer.register_failed_attempt(
                settings.LOGIN_MAX_ATTEMPTS,
                settings.LOGIN_LOCKOUT_MINUTES,
            )
            add_flash(request, "Invalid credentials.", "error")
            return render(request, "accounts/unified_login.html",
                          {"tab": "customer", "email": email,
                           "next": _safe_next(request, default_next)})

        customer.reset_failed_attempts()
        customer.last_login = timezone.now()
        customer.save(update_fields=["last_login"])
        login_customer(request, customer)
        add_flash(request, f"Welcome back, {customer.full_name}.", "success")
        return redirect(_safe_next(request, default_next))

    # GET
    return render(request, "accounts/unified_login.html", {
        "tab": tab,
        "next": _safe_next(request, "/staff/" if tab == "staff" else "/account/"),
    })


def unified_logout(request):
    """Log out of whichever session is active (or both if both)."""
    if get_current_staff(request) is not None:
        try:
            from audit.helpers import log as audit_log
            from audit.models import AuditLog
            audit_log(request, AuditLog.ACTION_LOGOUT, staff=get_current_staff(request))
        except Exception:
            pass
        logout_staff(request)

    if get_current_customer(request) is not None:
        logout_customer(request)

    add_flash(request, "You are signed out.", "info")
    return redirect("core:home")
