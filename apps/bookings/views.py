from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import Booking
from .permissions import IsAttendee
from .serializers import BookingCreateSerializer, BookingSerializer


class BookingViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Attendee: book seats and manage OWN bookings (looked up by reference)."""

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsAttendee]
    lookup_field = "reference"
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        # Only my bookings: someone else's reference returns 404.
        return Booking.objects.filter(attendee=self.request.user).select_related("event")

    @extend_schema(request=BookingCreateSerializer, responses={201: BookingSerializer})
    def create(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = services.create_booking(
            attendee=request.user,
            event_id=serializer.validated_data["event"],
            seats=serializer.validated_data["seats"],
        )
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=BookingSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, reference=None):
        booking = services.cancel_booking(booking=self.get_object())
        return Response(BookingSerializer(booking).data)