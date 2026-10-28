from django.utils import timezone
from rest_framework import serializers

from .models import Event

class PublicEventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source="organizer.username", read_only=True)
    seats_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "venue", "city", "start_at", "end_at",
            "capacity", "ticket_price", "seats_remaining", "organizer_name",
        ]

class OrganizerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "venue", "city", "start_at", "end_at",
            "capacity", "ticket_price", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]
        extra_kwargs = {
            "capacity": {"min_value": 1},
            "ticket_price": {"min_value": 0},
        }

    def validate(self, attrs):
        if self.instance and self.instance.status == Event.Status.CANCELLED:
            raise serializers.ValidationError("Cancelled events cannot be edited.")

        start = attrs.get("start_at", getattr(self.instance, "start_at", None))
        end = attrs.get("end_at", getattr(self.instance, "end_at", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"end_at": "End must be after start."})

        if "start_at" in attrs and attrs["start_at"] <= timezone.now():
            raise serializers.ValidationError({"start_at": "Start must be in the future."})


        if "capacity" in attrs and self.instance:
            from apps.bookings.services import confirmed_seats

            booked = confirmed_seats(self.instance)
            if attrs["capacity"] < booked:
                raise serializers.ValidationError(
                    {"capacity": f"Capacity cannot be below the {booked} seats already booked."}
                )
        return attrs

class OrganizerEventStatsSerializer(OrganizerEventSerializer):
    seats_booked = serializers.IntegerField(read_only=True)
    seats_remaining = serializers.IntegerField(read_only=True)
    confirmed_bookings = serializers.IntegerField(read_only=True)
    gross_revenue = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(OrganizerEventSerializer.Meta):
        fields = OrganizerEventSerializer.Meta.fields + [
            "seats_booked", "seats_remaining", "confirmed_bookings", "gross_revenue",
        ]
        read_only_fields = OrganizerEventSerializer.Meta.read_only_fields