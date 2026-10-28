from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class EventQuerySet(models.QuerySet):
    def published_upcoming(self):
        return self.filter(status=Event.Status.PUBLISHED, start_at__gt=timezone.now())


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="events"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=200)
    city = models.CharField(max_length=100, db_index=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["start_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")), name="event_end_after_start"
            ),
            models.CheckConstraint(condition=Q(capacity__gte=1), name="event_capacity_gte_1"),
            models.CheckConstraint(condition=Q(ticket_price__gte=0), name="event_price_gte_0"),
        ]
        indexes = [
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["organizer", "status"]),
        ]

    def __str__(self):
        return self.title