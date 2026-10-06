"""Bookings admin registrations."""

from django.contrib import admin

from apps.core.admin import AuditedModelAdmin

from .models import Booking, BookingAddOn


class BookingAddOnInline(admin.TabularInline):
    model = BookingAddOn
    extra = 0


@admin.register(Booking)
class BookingAdmin(AuditedModelAdmin):
    list_display = (
        "booking_reference",
        "customer",
        "vehicle",
        "pickup_branch",
        "pickup_datetime",
        "return_datetime",
        "status",
        "total_amount",
    )
    list_filter = ("status", "pickup_branch")
    search_fields = ("booking_reference", "customer__user__email", "vehicle__registration_no")
    date_hierarchy = "pickup_datetime"
    raw_id_fields = ("customer", "vehicle", "tariff")
    readonly_fields = ("blocked_period",)
    inlines = [BookingAddOnInline]


@admin.register(BookingAddOn)
class BookingAddOnAdmin(AuditedModelAdmin):
    list_display = ("booking", "add_on", "quantity", "daily_rate")
    list_filter = ("add_on",)
    search_fields = ("booking__booking_reference",)
    raw_id_fields = ("booking",)
