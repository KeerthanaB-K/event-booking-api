from rest_framework.permissions import BasePermission


class IsAttendee(BasePermission):
    message = "Only attendees can do this."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_attendee)