from django.conf import settings

from accounts.flash import pop_flashes


def site(request):
    """Exposes SITE_* settings + one-shot flash messages to every template."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "BookMyShaadi"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE", ""),
        "SITE_PHONE": getattr(settings, "SITE_PHONE", ""),
        "SITE_EMAIL": getattr(settings, "SITE_EMAIL", ""),
        "flashes": pop_flashes(request),
    }
