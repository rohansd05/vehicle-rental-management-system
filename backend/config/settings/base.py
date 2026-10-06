"""Settings shared by every environment.

Values come from backend/.env through django-environ (D5). See
backend/.env.example for the full list of variables.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# backend/.env wins over variables already in the OS environment, so a stray
# machine-wide SECRET_KEY or DATABASE_URL from another project cannot leak in.
# Without the file (e.g. a container given env vars), the OS environment is used.
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env", overwrite=True)

# ─── Core ────────────────────────────────────────────────
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Third party
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "django_celery_beat",
    # VRMS
    "apps.core",
    "apps.accounts",
    "apps.fleet",
    "apps.pricing",
    "apps.bookings",
    "apps.rentals",
    "apps.payments",
    "apps.maintenance",
    "apps.notifications",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ─── Database ────────────────────────────────────────────
# PostgreSQL only: the booking ExclusionConstraint (BR-1, Reliability-1)
# needs django.contrib.postgres.
DATABASES = {"default": env.db("DATABASE_URL")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Auth ────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.User"

# SE-2 / D4: bcrypt with a work factor of at least 12. The first entry hashes
# every new password.
PASSWORD_HASHERS = [
    "apps.accounts.hashers.BCryptSHA256Rounds12PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─── Time and locale (CO-6) ──────────────────────────────
# Timestamps are stored in UTC (USE_TZ=True). TIME_ZONE is used only to
# display local time; it never changes what is stored.
USE_TZ = True
TIME_ZONE = "Asia/Kolkata"
LANGUAGE_CODE = "en-us"
USE_I18N = True

# ─── Static and media ────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL_EXPIRY_SECONDS = env.int("MEDIA_URL_EXPIRY_SECONDS", default=900)

# ─── Agency (D7) ─────────────────────────────────────────
# The agency name is never hardcoded anywhere else; always read it from here.
AGENCY_NAME = env("AGENCY_NAME", default="[Agency Name]")
CURRENCY = env("CURRENCY", default="INR")

# ─── Django REST Framework ───────────────────────────────
# IsAuthenticated is only the safety net. Every view must still declare
# permission_classes explicitly (SE-4).
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

# TODO(SE-9): placeholder lifetimes. SE-9 requires a session to expire after
# 30 minutes of inactivity, and re-authentication before a payment or refund.
# Settle the token and refresh strategy in Phase 1.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=30),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# D12: /api/schema/ and /api/docs/ are public only when API_DOCS_PUBLIC is
# True (development). Otherwise they require an administrator; config/urls.py
# applies the permission classes.
API_DOCS_PUBLIC = False

SPECTACULAR_SETTINGS = {
    "TITLE": "Vehicle Rental Management System API",
    "DESCRIPTION": "REST + JSON API documented with OpenAPI 3.0 (CO-4).",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

# ─── Celery (broker and result backend: Valkey, D2) ──────
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ─── Integrations (sandbox only, CO-7) ───────────────────
# The factories in integrations/ pick the implementation from these names.
PAYMENT_GATEWAY_BACKEND = env("PAYMENT_GATEWAY_BACKEND", default="mock")
PAYMENT_GATEWAY_KEY_ID = env("PAYMENT_GATEWAY_KEY_ID", default="")
PAYMENT_GATEWAY_KEY_SECRET = env("PAYMENT_GATEWAY_KEY_SECRET", default="")

NOTIFICATION_BACKEND = env("NOTIFICATION_BACKEND", default="mock")
SMS_ACCOUNT_SID = env("SMS_ACCOUNT_SID", default="")
SMS_AUTH_TOKEN = env("SMS_AUTH_TOKEN", default="")

EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# ─── Logging ─────────────────────────────────────────────
# SE-2 / CO-2: never log passwords or card details.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
