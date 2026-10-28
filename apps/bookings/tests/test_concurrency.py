import threading

import pytest
from django.db import connection

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.services import create_booking
from apps.events.models import Event


@pytest.mark.django_db(transaction=True)
def test_concurrent_bookings_never_oversell(make_event):
    """10 attendees race for the last 5 seats: exactly 5 succeed, never more."""
    event = make_event(capacity=5)
    attendees = [
        User.objects.create_user(
            username=f"racer{i}", email=f"racer{i}@test.com",
            password="StrongPass#123", role=User.Role.ATTENDEE,
        )
        for i in range(10)
    ]

    results = []
    barrier = threading.Barrier(len(attendees))

    def worker(user):
        try:
            barrier.wait()  # start all threads at the same moment
            create_booking(attendee=user, event_id=event.id, seats=1)
            results.append("ok")
        except Exception:
            results.append("rejected")
        finally:
            connection.close()  # each thread has its own DB connection

    threads = [threading.Thread(target=worker, args=(u,)) for u in attendees]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    confirmed = sum(
        b.seats for b in Booking.objects.filter(event=event, status="confirmed")
    )
    assert confirmed == 5
    assert results.count("ok") == 5
    assert results.count("rejected") == 5
    assert Event.objects.get(pk=event.pk).capacity == 5