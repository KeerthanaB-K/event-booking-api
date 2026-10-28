from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.events.models import Event


def make_user(username, role):
    return User.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="StrongPass#123",
        role=role,
    )


def client_for(user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def organizer(db):
    return make_user("org_test", User.Role.ORGANIZER)


@pytest.fixture
def other_organizer(db):
    return make_user("org_other", User.Role.ORGANIZER)


@pytest.fixture
def attendee(db):
    return make_user("att_test", User.Role.ATTENDEE)


@pytest.fixture
def other_attendee(db):
    return make_user("att_other", User.Role.ATTENDEE)


@pytest.fixture
def org_client(organizer):
    return client_for(organizer)


@pytest.fixture
def other_org_client(other_organizer):
    return client_for(other_organizer)


@pytest.fixture
def att_client(attendee):
    return client_for(attendee)


@pytest.fixture
def other_att_client(other_attendee):
    return client_for(other_attendee)


@pytest.fixture
def anon_client():
    return APIClient()


@pytest.fixture
def make_event(organizer):
    def _make(**overrides):
        start = overrides.pop("start_at", timezone.now() + timedelta(days=10))
        data = {
            "organizer": organizer,
            "title": "Test Event",
            "description": "desc",
            "venue": "Hall",
            "city": "Mysuru",
            "start_at": start,
            "end_at": start + timedelta(hours=3),
            "capacity": 10,
            "ticket_price": 100,
            "status": Event.Status.PUBLISHED,
        }
        data.update(overrides)
        return Event.objects.create(**data)

    return _make