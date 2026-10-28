from rest_framework.routers import SimpleRouter

from .views import OrganizerEventViewSet

router = SimpleRouter()
router.register("organizer/events", OrganizerEventViewSet, basename="organizer-event")

urlpatterns = router.urls