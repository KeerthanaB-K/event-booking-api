from rest_framework.permissions import BasePermission


class IsOrganizer(BasePermission):
    message = "Only organizers can do this."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_organizer)