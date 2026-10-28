from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.services import create_booking
from apps.events.models import Event
from apps.events.services import cancel_event

PASSWORD = "DemoPass#123"
ORGANIZERS = ["demo_org1", "demo_org2"]
ATTENDEES = ["demo_att1", "demo_att2", "demo_att3"]

# (organizer index, title, city, days from now, capacity, price, state, seats per attendee)
EVENTS = [
    (0, "Bengaluru Python Meetup", "Bengaluru", 10, 100, "0", "published", (2, 1, 3)),
    (0, "Cloud Native Summit", "Bengaluru", 25, 300, "1500", "published", (4, 2)),
    (0, "Mysuru Food Festival", "Mysuru", 15, 200, "250", "published", (5,)),
    (0, "Sold Out Workshop", "Mysuru", 12, 5, "999", "published", (2, 3)),
    (0, "Upcoming Hackathon (draft)", "Bengaluru", 40, 150, "0", "draft", ()),
    (1, "Pune Jazz Night", "Pune", 20, 80, "700", "published", (2, 2, 1)),
    (1, "Startup Pitch Day", "Hyderabad", 30, 120, "0", "published", (1,)),
    (1, "Chennai Art Walk", "Chennai", 18, 60, "300", "published", ()),
    (1, "Cancelled Concert", "Pune", 22, 500, "2000", "cancelled", (2, 3)),
    (1, "Design Conf (draft)", "Hyderabad", 50, 250, "1200", "draft", ()),
]


class Command(BaseCommand):
    help = "Create demo users, events and bookings (safe to run more than once)."

    def _user(self, username, role):
        user = User.objects.filter(username=username).first()
        if user:
            return user
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=PASSWORD,
            role=role,
        )

    def handle(self, *args, **options):
        organizers = [self._user(n, User.Role.ORGANIZER) for n in ORGANIZERS]
        attendees = [self._user(n, User.Role.ATTENDEE) for n in ATTENDEES]
        now = timezone.now()
        created = 0

        for org_idx, title, city, days, capacity, price, state, seats_plan in EVENTS:
            organizer = organizers[org_idx]
            if Event.objects.filter(organizer=organizer, title=title).exists():
                continue

            start = (now + timedelta(days=days)).replace(
                hour=18, minute=0, second=0, microsecond=0
            )
            event = Event.objects.create(
                organizer=organizer,
                title=title,
                description=f"Demo event: {title}",
                venue=f"{city} Convention Centre",
                city=city,
                start_at=start,
                end_at=start + timedelta(hours=3),
                capacity=capacity,
                ticket_price=Decimal(price),
                status=Event.Status.DRAFT if state == "draft" else Event.Status.PUBLISHED,
            )
            for attendee, seats in zip(attendees, seats_plan):
                create_booking(attendee=attendee, event_id=event.pk, seats=seats)
            if state == "cancelled":
                cancel_event(event=event)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seed done. {created} new event(s) created."))
        self.stdout.write(f"Organizers: {', '.join(ORGANIZERS)}")
        self.stdout.write(f"Attendees:  {', '.join(ATTENDEES)}")
        self.stdout.write(f"Password for all demo users: {PASSWORD}")