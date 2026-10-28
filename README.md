# Event Booking API

Repository: https://github.com/KeerthanaB-K/event-booking-api

REST API (Django 5.2 + Django REST Framework + PostgreSQL) for selling seats to events.
Organizers publish events, attendees book seats, and the system never sells more seats
than an event has, even under concurrent requests.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

The API runs on http://localhost:8000. Migrations are applied automatically on start.

- Swagger docs: http://localhost:8000/api/docs/
- Django admin: http://localhost:8000/admin/

Create an admin user (gets the `admin` role automatically):

```bash
docker compose exec web python manage.py createsuperuser
```

Load demo data (safe to run more than once):

```bash
docker compose exec web python manage.py seed_demo
```

Demo users (password for all: `DemoPass#123`):
organizers `demo_org1`, `demo_org2`; attendees `demo_att1`, `demo_att2`, `demo_att3`.

## Run the tests

```bash
docker compose exec web pytest
```

Tests use a separate test database, so your data is never touched. They cover booking rules,
permissions, main API flows, the query count of the public list, and a concurrency test.

## Authentication

Token authentication. `POST /api/auth/register/` (role: `organizer` or `attendee`, never admin)
and `POST /api/auth/login/` both return a token. Send it as `Authorization: Token <token>`.
Browsing events is public; every other endpoint requires a token.

## Main endpoints

| Endpoint | Who |
|---|---|
| `GET /api/events/`, `GET /api/events/{id}/` | public |
| `GET/POST /api/organizer/events/`, `PATCH/DELETE .../{id}/` | organizer (own events) |
| `POST /api/organizer/events/{id}/publish/`, `.../cancel/` | organizer (owner) |
| `GET /api/organizer/events/{id}/bookings/` | organizer (owner) |
| `POST /api/bookings/`, `GET /api/bookings/`, `GET /api/bookings/{reference}/` | attendee |
| `POST /api/bookings/{reference}/cancel/` | attendee (owner) |

Public list filters: `city`, `start_after`, `start_before`, `min_price`, `max_price`, `free`;
`search` (title, description); `ordering` (`start_at`, `ticket_price`); pagination via `page`.

## How overselling is prevented

Booking runs inside one database transaction (`apps/bookings/services.py::create_booking`):

1. `SELECT ... FOR UPDATE` (`select_for_update()`) locks the event row. Concurrent bookings
   for the same event queue up behind this lock; other events are not blocked.
2. Inside the lock we check the business rules, then sum the confirmed seats with a database
   aggregate and insert the booking only if `booked + requested <= capacity`.
3. The transaction commits and releases the lock. The next request counts again and sees the
   new booking, so two requests can never both believe the last seat is free.

Database safety nets: a check constraint (seats between 1 and 5) and a partial unique
constraint (one confirmed booking per attendee per event). Cancelling an event and changing
its capacity take the same row lock.

`test_concurrent_bookings_never_oversell` starts 10 threads that race for 5 seats and asserts
exactly 5 succeed.

**Trade-off:** a row lock per event limits throughput on one extremely popular event. At this
scale that is acceptable and simple to reason about. An alternative is a `seats_booked`
counter updated with a conditional `UPDATE`.

## Design decisions

- **Service layer** (`services.py`): business rules live outside views and serializers.
- **Custom user** with a `role` field. `admin` role is assigned only to superusers created
  from the command line, never through the API.
- **Booking reference** (`BK-XXXXXXXX`) is random (`secrets`), unique, and used in URLs
  instead of the database id.
- **Price snapshot**: unit and total price are stored on the booking, so later price edits
  do not change past bookings.
- **No N+1**: seats booked/remaining, confirmed bookings and revenue are database aggregates
  (`Sum`/`Count` with `filter=`) in one query; a test checks the query count stays constant.
- **404 instead of 403** for other users' objects, so existence is not leaked.
- **Status codes**: 400 invalid input, 401 not logged in, 403 wrong role, 404 not found or not
  yours, 409 business-rule conflict (no seats, already booked, wrong state).
- Secrets come from environment variables; `.env` is git-ignored.

## Assumptions and limitations

- A confirmed booking is treated as paid; free events have a total of 0.
- A cancelled event cannot be re-published.
- All times are stored in UTC.
- Cancellation closes 24 hours before the event start.
- No payments, emails, rate limiting or caching.
- The development server is used in Docker; use a production WSGI server for deployment.