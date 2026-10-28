from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.events.models import Event

from .exceptions import (
    AlreadyBooked,
    AlreadyCancelled,
    CancellationWindowClosed,
    EventNotBookable,
    NotEnoughSeats,
)
from .models import Booking

CANCELLATION_WINDOW = timedelta(hours=24)


def confirmed_seats(event):
    """Total confirmed seats for an event, summed in the database."""
    return event.bookings.filter(status=Booking.Status.CONFIRMED).aggregate(
        total=Coalesce(Sum("seats"), 0)
    )["total"]


@transaction.atomic
def create_booking(*, attendee, event_id, seats):
    # 1. Lock the event row. Concurrent bookings for the SAME event wait here,
    #    one at a time. Bookings for other events are not blocked.
    try:
        event = Event.objects.select_for_update().get(pk=event_id)
    except Event.DoesNotExist:
        raise NotFound("Event not found.")

    # 2. Business rules (checked inside the lock).
    if event.status != Event.Status.PUBLISHED or event.start_at <= timezone.now():
        raise EventNotBookable()

    if event.bookings.filter(attendee=attendee, status=Booking.Status.CONFIRMED).exists():
        raise AlreadyBooked()

    # 3. Count confirmed seats INSIDE the lock, so the number cannot change
    #    between our check and our insert.
    booked = confirmed_seats(event)
    if booked + seats > event.capacity:
        raise NotEnoughSeats(f"Only {event.capacity - booked} seat(s) left.")

    # 4. Safe to insert.
    return Booking.objects.create(
        event=event,
        attendee=attendee,
        seats=seats,
        unit_price=event.ticket_price,
        total_price=event.ticket_price * seats,
    )


@transaction.atomic
def cancel_booking(*, booking):
    booking = (
        Booking.objects.select_for_update().select_related("event").get(pk=booking.pk)
    )
    if booking.status == Booking.Status.CANCELLED:
        raise AlreadyCancelled()
    if booking.event.start_at - timezone.now() < CANCELLATION_WINDOW:
        raise CancellationWindowClosed()

    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.save(update_fields=["status", "cancelled_at"])
    return booking