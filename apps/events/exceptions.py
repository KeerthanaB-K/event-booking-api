from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidStateTransition(APIException):
    """Action not allowed in the event's current status (HTTP 409)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "This action is not allowed in the current state."
    default_code = "invalid_state"