"""Pick the notification implementation from settings.NOTIFICATION_BACKEND."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .interface import NotificationService

BACKENDS = {
    "mock": "integrations.notification.mock.MockNotificationService",
}


def get_notification_service() -> NotificationService:
    name = settings.NOTIFICATION_BACKEND
    try:
        path = BACKENDS[name]
    except KeyError as exc:
        raise ImproperlyConfigured(
            f"Unknown NOTIFICATION_BACKEND {name!r}; expected one of {sorted(BACKENDS)}."
        ) from exc
    return import_string(path)()
