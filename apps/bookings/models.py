import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q

REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no confusing 0/O/1/I


def generate_reference():
    """Random, non-guessable reference like BK-7F3K9Q2M."""
    return "BK-" + "".join(secrets.choice(REFERENCE_ALPHABET) for _ in range(8))


class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.CharField(
        max_length=11, unique=True, default=generate_reference, editable=False
    )
    event = models.ForeignKey(
        "events.Event", on_delete=models.PROTECT, related_name="bookings"
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    seats = models.PositiveSmallIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(seats__gte=1, seats__lte=5), name="booking_seats_1_to_5"
            ),
            models.UniqueConstraint(
                fields=["event", "attendee"],
                condition=Q(status="confirmed"),
                name="one_confirmed_booking_per_attendee_event",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "status"]),
            models.Index(fields=["attendee", "status"]),
        ]

    def __str__(self):
        return self.reference