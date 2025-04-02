from django.urls import path, include

from rest_framework import routers

from train_station.views import JourneyViewSet, CrewMemberViewSet, StationViewSet, TrainViewSet, TrainTypeViewSet, \
    RouteViewSet

app_name = "train_station"

router = routers.DefaultRouter()
router.register("journeys", JourneyViewSet)
router.register("crews", CrewMemberViewSet)
router.register("stations", StationViewSet)
router.register("trains", TrainViewSet)
router.register("train-types", TrainTypeViewSet)
router.register("routes", RouteViewSet)


urlpatterns = [

    path("", include(router.urls))
]