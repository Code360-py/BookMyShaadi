"""
Create (or reset) an ADMIN staff account.

Usage:
    python manage.py create_admin admin@example.com "Full Name" "password123"
"""

import sys
from django.core.management.base import BaseCommand

from accounts.models import Staff


class Command(BaseCommand):
    help = "Create an ADMIN staff account"

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("full_name")
        parser.add_argument("password")

    def handle(self, *args, **opts):
        email = opts["email"].strip().lower()
        existing = Staff.objects.filter(email__iexact=email).first()

        if existing:
            existing.full_name = opts["full_name"]
            existing.set_password(opts["password"])
            existing.role = Staff.ROLE_ADMIN
            existing.is_active = True
            existing.must_change_password = False
            existing.failed_attempts = 0
            existing.locked_until = None
            existing.save()
            self.stdout.write(self.style.WARNING(f"Updated existing staff: {email}"))
            return

        s = Staff(
            email=email,
            full_name=opts["full_name"],
            role=Staff.ROLE_ADMIN,
            is_active=True,
        )
        s.set_password(opts["password"])
        s.save()
        self.stdout.write(self.style.SUCCESS(f"Created ADMIN: {email}"))
