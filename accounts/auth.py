"""
Session-based authentication for BookMyShaadi.

Two independent login "slots" live in the same session cookie:

    request.session["customer_id"]   → public customer login
    request.session["staff_id"]      → staff backend login

Helpers, decorators, and login/logout functions below.
No django.contrib.auth anywhere.
"""

from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from .models import Customer, Staff


# ===========================================================================
# Session key helpers
# ===========================================================================
def _customer_key() -> str:
    return getattr(settings, "SESSION_CUSTOMER_KEY", "customer_id")


def _staff_key() -> str:
    return getattr(settings, "SESSION_STAFF_KEY", "staff_id")


# ===========================================================================
# Customer login / logout
# ===========================================================================
def login_customer(request, customer: Customer) -> None:
    """Store the customer id in the session. Rotates the session id."""
    request.session.cycle_key()
    request.session[_customer_key()] = customer.id


def logout_customer(request) -> None:
    """Remove ONLY the customer slot; staff session (if any) stays intact."""
    key = _customer_key()
    if key in request.session:
        del request.session[key]


def get_current_customer(request):
    """Return the logged-in Customer, or None."""
    cid = request.session.get(_customer_key())
    if not cid:
        return None
    try:
        return Customer.objects.get(pk=cid, is_active=True)
    except Customer.DoesNotExist:
        logout_customer(request)
        return None


# ===========================================================================
# Staff login / logout
# ===========================================================================
def login_staff(request, staff: Staff) -> None:
    """Store the staff id in the session. Rotates the session id."""
    request.session.cycle_key()
    request.session[_staff_key()] = staff.id


def logout_staff(request) -> None:
    """Remove ONLY the staff slot."""
    key = _staff_key()
    if key in request.session:
        del request.session[key]


def get_current_staff(request):
    """Return the logged-in Staff, or None."""
    sid = request.session.get(_staff_key())
    if not sid:
        return None
    try:
        return Staff.objects.get(pk=sid, is_active=True)
    except Staff.DoesNotExist:
        logout_staff(request)
        return None


# ===========================================================================
# Decorators
# ===========================================================================
def customer_required(view_func):
    """
    Requires a logged-in customer.
    On fail: redirect to CUSTOMER_LOGIN_URL with ?next=... .
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_current_customer(request) is None:
            login_url = getattr(settings, "CUSTOMER_LOGIN_URL", "/login/?tab=customer")
            separator = "&" if "?" in login_url else "?"
            next_url = urlencode({"next": request.get_full_path()})
            return redirect(f"{login_url}{separator}{next_url}")
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """
    Requires a logged-in staff member (any role).
    On fail: redirect to STAFF_LOGIN_URL with ?next=... .
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if get_current_staff(request) is None:
            login_url = getattr(settings, "STAFF_LOGIN_URL", "/login/?tab=staff")
            separator = "&" if "?" in login_url else "?"
            next_url = urlencode({"next": request.get_full_path()})
            return redirect(f"{login_url}{separator}{next_url}")
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles: str):
    """
    Requires a logged-in staff member whose role is in `roles`.
    Use after (or with) @staff_required.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            staff = get_current_staff(request)
            if staff is None:
                login_url = getattr(settings, "STAFF_LOGIN_URL", "/login/?tab=staff")
                separator = "&" if "?" in login_url else "?"
                next_url = urlencode({"next": request.get_full_path()})
                return redirect(f"{login_url}{separator}{next_url}")
            if staff.role not in roles:
                return HttpResponseForbidden("You do not have access to this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
