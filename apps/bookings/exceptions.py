from rest_framework import status
from rest_framework.exceptions import APIException


class BookingError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "booking_error"


class EventNotBookable(BookingError):
    default_detail = "This event is not open for booking."


class AlreadyBooked(BookingError):
    default_detail = "You already have a confirmed booking for this event."


class NotEnoughSeats(BookingError):
    default_detail = "Not enough seats available."


class AlreadyCancelled(BookingError):
    default_detail = "This booking is already cancelled."


class CancellationWindowClosed(BookingError):
    default_detail = "Bookings cannot be cancelled within 24 hours of the event start."