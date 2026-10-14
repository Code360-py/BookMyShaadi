from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("packages/", views.packages, name="packages"),
    path("packages/<slug:slug>/", views.package_detail, name="package_detail"),
    path("vendors/", views.vendors, name="vendors"),
    path("gallery/", views.gallery, name="gallery"),
    path("contact/", views.contact, name="contact"),
]
