from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .exceptions import InvalidStateTransition
from .models import Event


@transaction.atomic
def publish_event(*, event):
    event = Event.objects.select_for_update().get(pk=event.pk)
    if event.status != Event.Status.DRAFT:
        raise InvalidStateTransition("Only draft events can be published.")
    if event.start_at <= timezone.now():
        raise ValidationError({"start_at": "Start must be in the future to publish."})
    event.status = Event.Status.PUBLISHED
    event.save(update_fields=["status", "updated_at"])
    return event


@transaction.atomic
def cancel_event(*, event):
    event = Event.objects.select_for_update().get(pk=event.pk)
    if event.status != Event.Status.PUBLISHED:
        raise InvalidStateTransition("Only published events can be cancelled.")
    event.status = Event.Status.CANCELLED
    event.save(update_fields=["status", "updated_at"])
    # Phase 4 adds here: cancel all confirmed bookings of this event.
    return event