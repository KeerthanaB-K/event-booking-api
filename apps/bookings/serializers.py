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