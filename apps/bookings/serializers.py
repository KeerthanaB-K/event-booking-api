from rest_framework import serializers

from .models import Booking


class BookingCreateSerializer(serializers.Serializer):
    event = serializers.IntegerField(help_text="Event id")
    seats = serializers.IntegerField(min_value=1, max_value=5)


class BookingSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "reference", "event", "event_title", "seats", "unit_price",
            "total_price", "status", "created_at", "cancelled_at",
        ]

class OrganizerBookingSerializer(serializers.ModelSerializer):
    attendee_name = serializers.SerializerMethodField()
    attendee_email = serializers.EmailField(source="attendee.email", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "reference", "attendee_name", "attendee_email", "seats",
            "total_price", "status", "created_at",
        ]

    def get_attendee_name(self, obj):
        return obj.attendee.get_full_name() or obj.attendee.username