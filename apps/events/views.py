from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .exceptions import InvalidStateTransition
from .models import Event
from .permissions import IsOrganizer
from .serializers import OrganizerEventSerializer


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
        return Event.objects.filter(organizer=self.request.user)

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
        return Response(self.get_serializer(event).data)

    @extend_schema(request=None, responses=OrganizerEventSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        event = services.cancel_event(event=self.get_object())
        return Response(self.get_serializer(event).data)