"""
Lightweight form helpers for enquiries.
Plain Python validation — no Django forms needed here.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

def validate_enquiry(data: dict) -> tuple[dict, list[str]]:
    """Return (cleaned, errors)."""
    errors: list[str] = []
    cleaned: dict = {}

    cleaned["full_name"] = (data.get("full_name") or "").strip()
    cleaned["email"] = (data.get("email") or "").strip().lower()
    cleaned["phone"] = (data.get("phone") or "").strip()

    if not cleaned["full_name"] or len(cleaned["full_name"]) > 255:
        errors.append("Enter a name with 1 to 255 characters.")
    try:
        EmailValidator()(cleaned["email"])
    except ValidationError:
        errors.append("A valid email is required.")
    if not cleaned["phone"]:
        errors.append("Phone is required.")
    elif len(cleaned["phone"]) > 20:
        errors.append("Phone number must be 20 characters or fewer.")

    # optional
    event_date = (data.get("event_date") or "").strip()
    cleaned["event_date"] = None
    if event_date:
        try:
            cleaned["event_date"] = date.fromisoformat(event_date)
        except ValueError:
            errors.append("Enter a valid event date.")

    cleaned["event_type"] = (data.get("event_type") or "WEDDING").strip().upper()
    valid_event_types = {"WEDDING", "ENGAGEMENT", "BIRTHDAY", "CORPORATE", "OTHER"}
    if cleaned["event_type"] not in valid_event_types:
        errors.append("Choose a valid event type.")
        cleaned["event_type"] = "WEDDING"

    guests = (data.get("guests") or "").strip()
    try:
        cleaned["guests"] = int(guests) if guests else None
    except ValueError:
        errors.append("Guests must be a number.")
        cleaned["guests"] = None
    if cleaned["guests"] is not None and not 0 < cleaned["guests"] <= 2_147_483_647:
        errors.append("Guests must be between 1 and 2,147,483,647.")

    budget = (data.get("budget") or "").strip()
    cleaned["budget"] = None
    if budget:
        try:
            cleaned["budget"] = Decimal(budget)
            if not cleaned["budget"].is_finite() or cleaned["budget"] < 0:
                raise InvalidOperation
            if cleaned["budget"].as_tuple().exponent < -2 or cleaned["budget"].adjusted() > 9:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            errors.append("Budget must be a valid non-negative amount with up to two decimal places.")
            cleaned["budget"] = None

    cleaned["message"] = (data.get("message") or "").strip()
    return cleaned, errors
