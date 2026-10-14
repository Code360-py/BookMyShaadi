from django.shortcuts import redirect
from django.urls import path

from . import views

app_name = "staffpanel"


def staff_login_redirect(request):
    q = request.GET.urlencode()
    url = "/login/?tab=staff"
    if q:
        url += f"&{q}"
    return redirect(url)

urlpatterns = [
    path("login/", staff_login_redirect, name="login"),
    path("logout/", views.staff_logout, name="logout"),  # view calls redirect to /login/ internally
    path("", views.dashboard, name="dashboard"),
    path("password/change/", views.force_password_change, name="force_password_change"),

    # Enquiries
    path("enquiries/", views.enquiry_list, name="enquiry_list"),
    path("enquiries/<int:pk>/", views.enquiry_detail, name="enquiry_detail"),
    path("enquiries/<int:pk>/status/", views.enquiry_update_status, name="enquiry_update_status"),
    path("enquiries/<int:pk>/convert/", views.enquiry_convert, name="enquiry_convert"),

    # Customers
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/<int:pk>/reset/", views.customer_reset_password, name="customer_reset_password"),
    path("customers/<int:pk>/toggle/", views.customer_toggle_active, name="customer_toggle_active"),

    # Bookings
    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/new/", views.booking_create, name="booking_create"),
    path("bookings/<int:pk>/", views.booking_detail, name="booking_detail"),
    path("bookings/<int:pk>/edit/", views.booking_edit, name="booking_edit"),

    # Events
    path("events/", views.event_list, name="event_list"),
    path("events/new/", views.event_create, name="event_create"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("events/<int:pk>/delete/", views.event_delete, name="event_delete"),

    # Vendors
    path("vendors/", views.vendor_list, name="vendor_list"),
    path("vendors/new/", views.vendor_create, name="vendor_create"),
    path("vendors/<int:pk>/", views.vendor_detail, name="vendor_detail"),
    path("vendors/<int:pk>/edit/", views.vendor_edit, name="vendor_edit"),
    path("vendors/<int:pk>/delete/", views.vendor_delete, name="vendor_delete"),

    # Collaborations
    path("collabs/", views.collab_list, name="collab_list"),
    path("collabs/new/", views.collab_create, name="collab_create"),
    path("collabs/<int:pk>/", views.collab_detail, name="collab_detail"),
    path("collabs/<int:pk>/edit/", views.collab_edit, name="collab_edit"),
    path("collabs/<int:pk>/delete/", views.collab_delete, name="collab_delete"),

    # Tasks
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/new/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/toggle/", views.task_toggle_status, name="task_toggle_status"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),

    # Expenses
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/new/", views.expense_create, name="expense_create"),
    path("expenses/<int:pk>/", views.expense_detail, name="expense_detail"),
    path("expenses/<int:pk>/edit/", views.expense_edit, name="expense_edit"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="expense_delete"),

    # Payments
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/new/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("payments/<int:pk>/edit/", views.payment_edit, name="payment_edit"),
    path("payments/<int:pk>/delete/", views.payment_delete, name="payment_delete"),

    # Audit
    path("audit/", views.audit_list, name="audit_list"),
    path("audit/<int:pk>/", views.audit_detail, name="audit_detail"),

    # Staff management (ADMIN only)
    path("staff/", views.staff_list, name="staff_list"),
    path("staff/new/", views.staff_create, name="staff_create"),
    path("staff/<int:pk>/", views.staff_detail, name="staff_detail"),
    path("staff/<int:pk>/edit/", views.staff_edit, name="staff_edit"),
    path("staff/<int:pk>/reset/", views.staff_reset_password, name="staff_reset_password"),
    path("staff/<int:pk>/toggle/", views.staff_toggle_active, name="staff_toggle_active"),
]
