"""
Django settings for BookMyShaadi.

Two-sided platform:
  - Public site + customer accounts  (session key: customer_id)
  - Private staff backend            (session key: staff_id)

Plain models — no django.contrib.auth for user management.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",

    # Project apps
    "accounts",
    "core",
    "bookings",
    "events",
    "vendors",
    "finance",
    "tasks",
    "staffpanel",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # our own — attached later
    # "audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "BookMyShaadi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "core.context_processors.site",
                "staffpanel.context_processors.staff_context",
            ],
        },
    },
]

WSGI_APPLICATION = "BookMyShaadi.wsgi.application"
ASGI_APPLICATION = "BookMyShaadi.asgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
# Two independent session "slots" — one per user type.
# We store both keys in the same session cookie, namespaced:
#   session["customer_id"]  → public/customer login
#   session["staff_id"]     → staff backend login
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30          # 30 days for customers
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG               # HTTPS-only in prod


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG


# ---------------------------------------------------------------------------
# Security hardening (only active when DEBUG=False)
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# ---------------------------------------------------------------------------
# Auth-related redirect targets (used by our own decorators)
# ---------------------------------------------------------------------------
CUSTOMER_LOGIN_URL = "/login/?tab=customer"
STAFF_LOGIN_URL = "/login/?tab=staff"

SESSION_CUSTOMER_KEY = "customer_id"
SESSION_STAFF_KEY = "staff_id"


# ---------------------------------------------------------------------------
# Password hashing (stdlib PBKDF2; we do it ourselves)
# ---------------------------------------------------------------------------
PASSWORD_HASH_ITERATIONS = 260_000


# ---------------------------------------------------------------------------
# Login throttle
# ---------------------------------------------------------------------------
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15


# ---------------------------------------------------------------------------
# Email (dev: print to console; override in prod)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DJANGO_DEFAULT_FROM_EMAIL", "noreply@bookmyshaadi.local"
)


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Site metadata (used by core.context_processors.site)
# ---------------------------------------------------------------------------
SITE_NAME = "BookMyShaadi"
SITE_TAGLINE = "Plan the wedding of your dreams"
SITE_PHONE = "+91 00000 00000"
SITE_EMAIL = "hello@bookmyshaadi.local"
