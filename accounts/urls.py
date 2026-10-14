from django.shortcuts import redirect
from django.urls import path

from . import unified_views, views

app_name = "accounts"


def redirect_to_unified_login(request, tab="customer"):
    q = request.GET.urlencode()
    url = f"/login/?tab={tab}"
    if q:
        url += f"&{q}"
    return redirect(url)


def legacy_customer_login(request):
    return redirect_to_unified_login(request, "customer")


def legacy_staff_login(request):
    return redirect_to_unified_login(request, "staff")


urlpatterns = [
    # Customer self-registration
    path("register/", views.register, name="register"),

    # Customer area
    path("", views.dashboard, name="dashboard"),
    path("events/", views.my_events, name="my_events"),
    path("events/<int:pk>/", views.my_event_detail, name="my_event_detail"),
    path("bookings/", views.my_bookings, name="my_bookings"),
    path("profile/", views.profile, name="profile"),
    path("password/", views.change_password, name="change_password"),

    # Customer logout (still works if a customer somehow hits the old URL)
    path("logout/", unified_views.unified_logout, name="logout"),
]
