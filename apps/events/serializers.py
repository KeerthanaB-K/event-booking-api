from django.utils import timezone
from rest_framework import serializers

from .models import Event


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

        # Phase 4 adds here: capacity cannot go below the seats already booked.
        return attrs