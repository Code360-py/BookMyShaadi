from django.urls import include, path

from accounts import unified_views

urlpatterns = [
    # Unified login / logout at the site root
    path("login/", unified_views.unified_login, name="login"),
    path("logout/", unified_views.unified_logout, name="logout"),

    # Public site
    path("", include("core.urls")),

    # Customer area (dashboard, profile, my-events, etc.)
    path("account/", include("accounts.urls")),

    # Public enquiry
    path("", include("bookings.urls")),

    # Staff backend (its own /staff/login/ redirects to /login/?tab=staff now)
    path("staff/", include("staffpanel.urls")),
]
