import pytest

pytestmark = pytest.mark.django_db

EVENT_BODY = {
    "title": "New Event",
    "description": "d",
    "venue": "Hall",
    "city": "Mysuru",
    "start_at": "2030-12-25T15:00:00Z",
    "end_at": "2030-12-25T18:00:00Z",
    "capacity": 10,
    "ticket_price": "0",
}


def test_anonymous_gets_401_on_protected_endpoints(anon_client):
    assert anon_client.get("/api/organizer/events/").status_code == 401
    assert anon_client.get("/api/bookings/").status_code == 401
    assert anon_client.post("/api/bookings/", {"event": 1, "seats": 1}, format="json").status_code == 401


def test_public_listing_needs_no_login(anon_client, make_event):
    make_event()
    res = anon_client.get("/api/events/")
    assert res.status_code == 200
    assert res.data["count"] == 1


def test_attendee_cannot_create_event(att_client):
    assert att_client.post("/api/organizer/events/", EVENT_BODY, format="json").status_code == 403


def test_organizer_cannot_book(org_client, make_event):
    event = make_event()
    res = org_client.post("/api/bookings/", {"event": event.id, "seats": 1}, format="json")
    assert res.status_code == 403


def test_organizer_can_create_event(org_client):
    res = org_client.post("/api/organizer/events/", EVENT_BODY, format="json")
    assert res.status_code == 201
    assert res.data["status"] == "draft"


def test_other_organizer_cannot_see_or_change_event(other_org_client, make_event):
    event = make_event()
    url = f"/api/organizer/events/{event.id}/"
    assert other_org_client.get(url).status_code == 404
    assert other_org_client.patch(url, {"title": "x"}, format="json").status_code == 404
    assert other_org_client.delete(url).status_code == 404
    assert other_org_client.post(f"{url}cancel/").status_code == 404
    assert other_org_client.get(f"{url}bookings/").status_code == 404


def test_attendee_cannot_see_other_attendees_booking(att_client, other_att_client, make_event):
    event = make_event()
    ref = att_client.post("/api/bookings/", {"event": event.id, "seats": 1}, format="json").data["reference"]
    assert other_att_client.get(f"/api/bookings/{ref}/").status_code == 404
    assert other_att_client.post(f"/api/bookings/{ref}/cancel/").status_code == 404
    assert other_att_client.get("/api/bookings/").data["count"] == 0


def test_attendee_cannot_open_organizer_bookings_list(att_client, make_event):
    event = make_event()
    assert att_client.get(f"/api/organizer/events/{event.id}/bookings/").status_code == 403


def test_cannot_register_as_admin(anon_client):
    res = anon_client.post(
        "/api/auth/register/",
        {"username": "evil", "email": "evil@test.com", "password": "StrongPass#123", "role": "admin"},
        format="json",
    )
    assert res.status_code == 400