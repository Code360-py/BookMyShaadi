from django.shortcuts import redirect, render

from accounts.flash import add_flash

from .forms import validate_enquiry
from .models import Enquiry


def _client_ip(request) -> str | None:
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def enquiry_create(request):
    """Public enquiry form — no login required."""
    if request.method == "POST":
        cleaned, errors = validate_enquiry(request.POST)
        if errors:
            for e in errors:
                add_flash(request, e, "error")
            return render(request, "bookings/enquiry_form.html", {
                "data": request.POST,
                "nav": "enquire",
            })

        Enquiry.objects.create(
            full_name=cleaned["full_name"],
            email=cleaned["email"],
            phone=cleaned["phone"],
            event_date=cleaned["event_date"] or None,
            event_type=cleaned["event_type"],
            guests=cleaned["guests"],
            budget=cleaned["budget"],
            message=cleaned["message"],
            ip_address=_client_ip(request),
        )
        add_flash(request, "Thank you! We'll be in touch shortly.", "success")
        return redirect("bookings:enquiry_thanks")

    return render(request, "bookings/enquiry_form.html", {"nav": "enquire"})


def enquiry_thanks(request):
    return render(request, "bookings/enquiry_thanks.html", {})
