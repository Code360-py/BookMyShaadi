"""
Plain models for the two user types:

  - Customer : self-registers on the public site
  - Staff    : created by an Admin; logs into the backend

No django.contrib.auth anywhere.
"""

from django.db import models
from django.utils import timezone

from .security import (
    generate_temp_password,
    hash_password,
    verify_password,
)


# ===========================================================================
# CUSTOMER — public user
# ===========================================================================
class Customer(models.Model):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)

    password = models.CharField(max_length=255)  # pbkdf2 hash
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)

    # lockout
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    # ---- password ----
    def set_password(self, raw: str) -> None:
        self.password = hash_password(raw)

    def check_password(self, raw: str) -> bool:
        return verify_password(raw, self.password)

    # ---- lockout ----
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failed_attempt(self, max_attempts: int, lock_minutes: int) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=lock_minutes)
        self.save(update_fields=["failed_attempts", "locked_until"])

    def reset_failed_attempts(self) -> None:
        if self.failed_attempts or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_attempts", "locked_until"])

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


# ===========================================================================
# STAFF — internal user
# ===========================================================================
class Staff(models.Model):
    ROLE_ADMIN = "ADMIN"
    ROLE_MANAGER = "MANAGER"
    ROLE_STAFF = "STAFF"
    ROLE_CHOICES = (
        (ROLE_ADMIN, "Admin"),
        (ROLE_MANAGER, "Manager"),
        (ROLE_STAFF, "Staff"),
    )

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)

    password = models.CharField(max_length=255)  # pbkdf2 hash
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STAFF)

    is_active = models.BooleanField(default=True)
    must_change_password = models.BooleanField(
        default=False,
        help_text="Set when admin resets password; forces change on next login.",
    )

    # lockout
    failed_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["role", "full_name"]

    # ---- password ----
    def set_password(self, raw: str) -> None:
        self.password = hash_password(raw)

    def check_password(self, raw: str) -> bool:
        return verify_password(raw, self.password)

    def reset_password_to_temp(self) -> str:
        """Admin-initiated reset. Returns the plaintext temp password."""
        temp = generate_temp_password()
        self.set_password(temp)
        self.must_change_password = True
        self.failed_attempts = 0
        self.locked_until = None
        self.save(update_fields=[
            "password", "must_change_password", "failed_attempts", "locked_until"
        ])
        return temp

    # ---- role helpers ----
    @property
    def is_admin(self) -> bool:
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == self.ROLE_MANAGER

    @property
    def is_staff_role(self) -> bool:
        return self.role == self.ROLE_STAFF

    def has_role(self, *roles: str) -> bool:
        return self.role in roles

    # ---- lockout ----
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failed_attempt(self, max_attempts: int, lock_minutes: int) -> None:
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=lock_minutes)
        self.save(update_fields=["failed_attempts", "locked_until"])

    def reset_failed_attempts(self) -> None:
        if self.failed_attempts or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_attempts", "locked_until"])

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_role_display()})"
