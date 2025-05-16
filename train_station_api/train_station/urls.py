from django.urls import path, include

from rest_framework import routers

from train_station.views import (
    JourneyViewSet,
    CrewMemberViewSet,
    StationViewSet,
    TrainViewSet,
    TrainTypeViewSet,
    RouteViewSet,
    RouteJourneysViewSet,
    JourneySearchView,
)

app_name = "train_station"


route_journeys_list = RouteJourneysViewSet.as_view(
    {"get": "list", "post": "create"}
)

route_journey_detail = RouteJourneysViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

router = routers.DefaultRouter()
router.register("journeys", JourneyViewSet)
router.register("crews", CrewMemberViewSet)
router.register("stations", StationViewSet)
router.register("trains", TrainViewSet)
router.register("train-types", TrainTypeViewSet)
router.register("routes", RouteViewSet),


urlpatterns = [
    path("", include(router.urls)),
    path(
        "route/<int:route_id>/journeys/",
        route_journeys_list,
        name="route-journeys-list",
    ),
    path(
        "route/<int:route_id>/journeys/<int:journey_id>",
        route_journey_detail,
        name="route-journey-detail",
    ),
    path(
        "search-journeys/", JourneySearchView.as_view(), name="search-journeys"
    ),
]
