from rest_framework.routers import SimpleRouter

from .views import OrganizerEventViewSet, PublicEventViewSet

router = SimpleRouter()
router.register("events", PublicEventViewSet, basename="event")
router.register("organizer/events", OrganizerEventViewSet, basename="organizer-event")

urlpatterns = router.urls