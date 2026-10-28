from datetime import timedelta

import pytest
from django.utils import timezone

from apps.bookings.models import Booking
from apps.events.models import Event

pytestmark = pytest.mark.django_db


def book(client, event_id, seats):
    return client.post("/api/bookings/", {"event": event_id, "seats": seats}, format="json")


def test_book_success_has_reference_and_price(att_client, make_event):
    event = make_event(ticket_price=499)
    res = book(att_client, event.id, 2)
    assert res.status_code == 201
    assert res.data["reference"].startswith("BK-")
    assert res.data["total_price"] == "998.00"
    assert res.data["status"] == "confirmed"


@pytest.mark.parametrize("seats", [0, 6])
def test_seats_must_be_between_1_and_5(att_client, make_event, seats):
    event = make_event()
    assert book(att_client, event.id, seats).status_code == 400


def test_cannot_book_more_than_capacity(att_client, make_event):
    event = make_event(capacity=2)
    res = book(att_client, event.id, 3)
    assert res.status_code == 409


def test_can_book_exactly_up_to_capacity(att_client, other_att_client, make_event):
    event = make_event(capacity=3)
    assert book(att_client, event.id, 2).status_code == 201
    assert book(other_att_client, event.id, 1).status_code == 201
    assert book(other_att_client, event.id, 1).status_code == 409  # already booked


def test_sold_out_event_rejects_new_booking(att_client, other_att_client, make_event):
    event = make_event(capacity=2)
    assert book(att_client, event.id, 2).status_code == 201
    assert book(other_att_client, event.id, 1).status_code == 409


def test_one_confirmed_booking_per_attendee_per_event(att_client, make_event):
    event = make_event()
    assert book(att_client, event.id, 1).status_code == 201
    assert book(att_client, event.id, 1).status_code == 409


def test_cannot_book_draft_cancelled_or_started_event(att_client, make_event):
    draft = make_event(status=Event.Status.DRAFT)
    cancelled = make_event(status=Event.Status.CANCELLED)
    started = make_event(start_at=timezone.now() - timedelta(hours=1))
    assert book(att_client, draft.id, 1).status_code == 409
    assert book(att_client, cancelled.id, 1).status_code == 409
    assert book(att_client, started.id, 1).status_code == 409


def test_unknown_event_returns_404(att_client):
    assert book(att_client, 999999, 1).status_code == 404


def test_cancel_frees_seats_and_allows_rebooking(att_client, other_att_client, make_event):
    event = make_event(capacity=2)
    first = book(att_client, event.id, 2)
    assert book(other_att_client, event.id, 1).status_code == 409

    cancel = att_client.post(f"/api/bookings/{first.data['reference']}/cancel/")
    assert cancel.status_code == 200
    assert cancel.data["status"] == "cancelled"

    assert book(other_att_client, event.id, 2).status_code == 201


def test_cancel_twice_returns_409(att_client, make_event):
    event = make_event()
    ref = book(att_client, event.id, 1).data["reference"]
    assert att_client.post(f"/api/bookings/{ref}/cancel/").status_code == 200
    assert att_client.post(f"/api/bookings/{ref}/cancel/").status_code == 409


def test_cannot_cancel_within_24_hours(att_client, make_event):
    event = make_event(start_at=timezone.now() + timedelta(hours=5))
    ref = book(att_client, event.id, 1).data["reference"]
    res = att_client.post(f"/api/bookings/{ref}/cancel/")
    assert res.status_code == 409
    assert Booking.objects.get(reference=ref).status == "confirmed"


def test_cancelling_event_cancels_its_bookings(org_client, att_client, make_event):
    event = make_event()
    ref = book(att_client, event.id, 2).data["reference"]

    res = org_client.post(f"/api/organizer/events/{event.id}/cancel/")
    assert res.status_code == 200

    booking = Booking.objects.get(reference=ref)
    assert booking.status == "cancelled"
    assert booking.cancelled_at is not None


def test_capacity_cannot_drop_below_booked_seats(org_client, att_client, make_event):
    event = make_event(capacity=10)
    book(att_client, event.id, 3)
    assert org_client.patch(
        f"/api/organizer/events/{event.id}/", {"capacity": 2}, format="json"
    ).status_code == 400
    assert org_client.patch(
        f"/api/organizer/events/{event.id}/", {"capacity": 3}, format="json"
    ).status_code == 200