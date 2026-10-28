from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # createsuperuser command always makes role = admin
        extra_fields.setdefault("role", User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        ATTENDEE = "attendee", "Attendee"
        ADMIN = "admin", "Admin"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATTENDEE)

    objects = CustomUserManager()

    @property
    def is_organizer(self):
        return self.role == self.Role.ORGANIZER

    @property
    def is_attendee(self):
        return self.role == self.Role.ATTENDEE