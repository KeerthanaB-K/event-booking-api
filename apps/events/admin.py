from django.contrib import admin

from apps.bookings.models import Booking

from .models import Event


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ("reference", "attendee", "seats", "total_price", "status", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title", "organizer", "city", "start_at", "capacity",
        "seats_booked", "seats_remaining", "ticket_price", "status",
    )
    list_filter = ("status", "city", "start_at")
    search_fields = ("title", "description", "venue", "organizer__username", "organizer__email")
    date_hierarchy = "start_at"
    autocomplete_fields = ("organizer",)
    inlines = [BookingInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("organizer").with_seat_stats()

    @admin.display(ordering="seats_booked")
    def seats_booked(self, obj):
        return obj.seats_booked

    @admin.display(ordering="seats_remaining")
    def seats_remaining(self, obj):
        return obj.seats_remaining