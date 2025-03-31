from django.urls import path, include

from rest_framework import routers

from train_station.views import JourneyViewSet, CrewMemberViewSet, StationViewSet

app_name = "train_station"

router = routers.DefaultRouter()
router.register("journeys", JourneyViewSet)
router.register("crew", CrewMemberViewSet)
router.register("station", StationViewSet)


urlpatterns = [

    path("", include(router.urls))
]