from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("enquiry/", views.enquiry_create, name="enquiry_create"),
    path("enquiry/thanks/", views.enquiry_thanks, name="enquiry_thanks"),
]
