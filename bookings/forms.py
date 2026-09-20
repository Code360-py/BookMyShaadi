"""
Lightweight form helpers for enquiries.
Plain Python validation — no Django forms needed here.
"""


def validate_enquiry(data: dict) -> tuple[dict, list[str]]:
    """Return (cleaned, errors)."""
    errors: list[str] = []
    cleaned: dict = {}

    cleaned["full_name"] = (data.get("full_name") or "").strip()
    cleaned["email"] = (data.get("email") or "").strip().lower()
    cleaned["phone"] = (data.get("phone") or "").strip()

    if not cleaned["full_name"]:
        errors.append("Full name is required.")
    if not cleaned["email"] or "@" not in cleaned["email"]:
        errors.append("A valid email is required.")
    if not cleaned["phone"]:
        errors.append("Phone is required.")

    # optional
    date = (data.get("event_date") or "").strip()
    cleaned["event_date"] = date or None

    cleaned["event_type"] = (data.get("event_type") or "WEDDING").strip().upper()

    guests = (data.get("guests") or "").strip()
    try:
        cleaned["guests"] = int(guests) if guests else None
    except ValueError:
        errors.append("Guests must be a number.")
        cleaned["guests"] = None

    budget = (data.get("budget") or "").strip()
    try:
        cleaned["budget"] = budget or None
    except ValueError:
        errors.append("Budget must be a number.")
        cleaned["budget"] = None

    cleaned["message"] = (data.get("message") or "").strip()
    return cleaned, errors
