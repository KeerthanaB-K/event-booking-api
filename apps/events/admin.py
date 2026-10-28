from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "city", "start_at", "capacity", "ticket_price", "status")
    list_filter = ("status", "city", "start_at")
    search_fields = ("title", "description", "venue", "organizer__username", "organizer__email")
    date_hierarchy = "start_at"
    autocomplete_fields = ("organizer",)