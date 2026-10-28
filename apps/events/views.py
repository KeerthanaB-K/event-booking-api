from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.bookings.serializers import OrganizerBookingSerializer

from . import services
from .exceptions import InvalidStateTransition
from .filters import EventFilter
from .models import Event
from .permissions import IsOrganizer
from .serializers import (
    OrganizerEventSerializer,
    OrganizerEventStatsSerializer,
    PublicEventSerializer,
)


class PublicEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Public: browse published events (no login needed)."""

    serializer_class = PublicEventSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    filterset_class = EventFilter
    search_fields = ["title", "description"]
    ordering_fields = ["start_at", "ticket_price"]
    ordering = ["start_at"]

    def get_queryset(self):
        qs = Event.objects.select_related("organizer").with_seat_stats()
        if self.action == "list":
            return qs.published_upcoming()
        return qs.filter(status=Event.Status.PUBLISHED)


class OrganizerEventViewSet(viewsets.ModelViewSet):
    """Organizer: manage OWN events only."""

    serializer_class = OrganizerEventSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    search_fields = ["title"]
    ordering_fields = ["start_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Event.objects.none()
        # Only my events: someone else's event simply returns 404.
        return Event.objects.filter(organizer=self.request.user).with_seat_stats()

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return OrganizerEventStatsSerializer
        return OrganizerEventSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != Event.Status.DRAFT:
            raise InvalidStateTransition("Only draft events can be deleted. Cancel it instead.")
        instance.delete()

    @extend_schema(request=None, responses=OrganizerEventSerializer)
    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        event = services.publish_event(event=self.get_object())
        return Response(OrganizerEventSerializer(event).data)

    @extend_schema(request=None, responses=OrganizerEventSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        event = services.cancel_event(event=self.get_object())
        return Response(OrganizerEventSerializer(event).data)

    @extend_schema(responses=OrganizerBookingSerializer(many=True))
    @action(detail=True, methods=["get"])
    def bookings(self, request, pk=None):
        event = self.get_object()
        qs = event.bookings.select_related("attendee").order_by("-created_at")
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(OrganizerBookingSerializer(page, many=True).data)