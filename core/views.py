from django.shortcuts import render

from events.models import Package, GalleryImage
from vendors.models import Vendor


def home(request):
    packages = Package.objects.filter(is_active=True)[:3]
    vendors = Vendor.objects.filter(is_active=True)[:6]
    gallery = GalleryImage.objects.filter(is_active=True)[:6]
    return render(request, "core/home.html", {
        "packages": packages,
        "featured_vendors": vendors,
        "gallery": gallery,
    })


def about(request):
    return render(request, "core/about.html", {})


def services(request):
    return render(request, "core/services.html", {})


def packages(request):
    return render(request, "core/packages.html", {
        "packages": Package.objects.filter(is_active=True),
        "nav": "packages",
    })


def package_detail(request, slug):
    from django.shortcuts import get_object_or_404
    pkg = get_object_or_404(Package, slug=slug, is_active=True)
    return render(request, "core/package_detail.html", {"package": pkg, "nav": "packages"})


def vendors(request):
    return render(request, "core/vendors.html", {
        "vendors": Vendor.objects.filter(is_active=True).order_by("name"),
        "nav": "vendors",
    })


def gallery(request):
    return render(request, "core/gallery.html", {
        "images": GalleryImage.objects.filter(is_active=True),
        "nav": "gallery",
    })


def contact(request):
    return render(request, "core/contact.html", {"nav": "contact"})
