"""Local development: Django runs natively; Postgres and Valkey run in Docker (D3)."""

from .base import *  # noqa: F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

DEBUG = env.bool("DEBUG", default=True)

# D12: API schema and Swagger UI are public in development only.
API_DOCS_PUBLIC = True

INSTALLED_APPS = [*INSTALLED_APPS, "debug_toolbar", "django_extensions"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware", *MIDDLEWARE]
INTERNAL_IPS = ["127.0.0.1"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
