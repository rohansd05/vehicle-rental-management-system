"""Helpers for writing audit entries (Fleet.Audit, SE-10)."""

from django.db import models

# Never copied into an audit entry (SE-2, CO-2).
SECRET_FIELDS = frozenset({"password", "code_hash", "card_token"})


def snapshot(instance: models.Model) -> dict:
    """The concrete field values of `instance`, ready for AuditLog.before/after."""
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in SECRET_FIELDS:
            continue
        value = getattr(instance, field.attname)
        if isinstance(field, models.FileField):
            value = value.name if value else ""
        data[field.attname] = value
    return data


def entity_type(instance: models.Model) -> str:
    return instance._meta.label
