from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.events.models import Event

pytestmark = pytest.mark.django_db


def test_validation_errors_on_create(org_client):
    base = {
        "title": "T", "description": "", "venue": "V", "city": "C",
        "start_at": "2030-12-25T15:00:00Z", "end_at": "2030-12-25T18:00:00Z",
        "capacity": 10, "ticket_price": "0",
    }
    assert org_client.post("/api/organizer/events/", {**base, "end_at": "2030-12-25T10:00:00Z"}, format="json").status_code == 400
    assert org_client.post("/api/organizer/events/", {**base, "capacity": 0}, format="json").status_code == 400
    assert org_client.post(
        "/api/organizer/events/",
        {**base, "start_at": "2020-01-01T10:00:00Z", "end_at": "2020-01-01T12:00:00Z"},
        format="json",
    ).status_code == 400


def test_lifecycle_draft_publish_cancel_delete_rules(org_client, make_event):
    draft = make_event(status=Event.Status.DRAFT)
    url = f"/api/organizer/events/{draft.id}/"

    assert org_client.post(f"{url}publish/").status_code == 200
    assert org_client.post(f"{url}publish/").status_code == 409
    assert org_client.delete(url).status_code == 409  # published cannot be deleted

    assert org_client.post(f"{url}cancel/").status_code == 200
    assert org_client.post(f"{url}cancel/").status_code == 409
    assert org_client.patch(url, {"title": "x"}, format="json").status_code == 400  # cancelled


def test_draft_can_be_deleted(org_client, make_event):
    draft = make_event(status=Event.Status.DRAFT)
    assert org_client.delete(f"/api/organizer/events/{draft.id}/").status_code == 204


def test_public_list_hides_draft_cancelled_and_past(anon_client, make_event):
    make_event(title="visible")
    make_event(title="draft", status=Event.Status.DRAFT)
    make_event(title="cancelled", status=Event.Status.CANCELLED)
    make_event(title="past", start_at=timezone.now() - timedelta(days=1))
    res = anon_client.get("/api/events/")
    assert [e["title"] for e in res.data["results"]] == ["visible"]


def test_public_list_filters_search_and_ordering(anon_client, make_event):
    make_event(title="Python Meetup", city="Bengaluru", ticket_price=0)
    make_event(title="Jazz Night", city="Mysuru", ticket_price=500)

    assert anon_client.get("/api/events/?city=mysuru").data["count"] == 1
    assert anon_client.get("/api/events/?free=true").data["results"][0]["title"] == "Python Meetup"
    assert anon_client.get("/api/events/?min_price=100").data["results"][0]["title"] == "Jazz Night"
    assert anon_client.get("/api/events/?search=python").data["count"] == 1
    titles = [e["title"] for e in anon_client.get("/api/events/?ordering=-ticket_price").data["results"]]
    assert titles == ["Jazz Night", "Python Meetup"]


def test_seats_remaining_in_public_list(anon_client, att_client, make_event):
    event = make_event(capacity=10)
    att_client.post("/api/bookings/", {"event": event.id, "seats": 4}, format="json")
    res = anon_client.get("/api/events/")
    assert res.data["results"][0]["seats_remaining"] == 6


def test_public_list_query_count_does_not_grow(anon_client, make_event, django_assert_num_queries):
    def count_queries(client):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            assert client.get("/api/events/").status_code == 200
        return len(ctx)

    for i in range(3):
        make_event(title=f"E{i}")
    few = count_queries(anon_client)

    for i in range(20):
        make_event(title=f"More{i}")
    many = count_queries(anon_client)

    assert few == many


def test_organizer_dashboard_stats(org_client, att_client, other_att_client, make_event):
    event = make_event(capacity=10, ticket_price=100)
    att_client.post("/api/bookings/", {"event": event.id, "seats": 2}, format="json")
    ref = other_att_client.post("/api/bookings/", {"event": event.id, "seats": 3}, format="json").data["reference"]
    other_att_client.post(f"/api/bookings/{ref}/cancel/")  # cancelled must not count

    res = org_client.get("/api/organizer/events/")
    row = res.data["results"][0]
    assert row["seats_booked"] == 2
    assert row["seats_remaining"] == 8
    assert row["confirmed_bookings"] == 1
    assert row["gross_revenue"] == "200.00"


def test_organizer_sees_bookings_with_attendee_details(org_client, att_client, make_event):
    event = make_event()
    att_client.post("/api/bookings/", {"event": event.id, "seats": 1}, format="json")
    res = org_client.get(f"/api/organizer/events/{event.id}/bookings/")
    assert res.status_code == 200
    row = res.data["results"][0]
    assert row["attendee_email"] == "att_test@test.com"
    assert row["status"] == "confirmed"


def test_register_and_login_flow(anon_client):
    body = {"username": "newuser", "email": "new@test.com", "password": "StrongPass#123", "role": "attendee"}
    reg = anon_client.post("/api/auth/register/", body, format="json")
    assert reg.status_code == 201
    assert reg.data["token"]

    login = anon_client.post(
        "/api/auth/login/", {"username": "newuser", "password": "StrongPass#123"}, format="json"
    )
    assert login.status_code == 200
    assert login.data["token"] == reg.data["token"]
    assert User.objects.get(username="newuser").role == "attendee"