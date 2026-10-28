from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "event", "attendee", "seats", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "attendee__username", "attendee__email", "event__title")
    readonly_fields = ("reference", "created_at", "cancelled_at")
    autocomplete_fields = ("event", "attendee")
    list_select_related = ("event", "attendee")