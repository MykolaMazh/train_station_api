from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, generics, mixins, viewsets
from rest_framework.views import APIView

from train_station.models import (
    Journey,
    CrewMember,
    Station,
    Train,
    TrainType,
    Route,
    Order,
)
from train_station.serializers import (
    JourneySerializer,
    CrewMemberSerializer,
    StationSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainTypeSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    RouteJourneysSerializer,
    RouteJourneysListSerializer,
    JourneySearchSerializer,
    OrderSerializer,
)
from train_station.utils import find_journeys_between_stations


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer
    # permission_classes = (IsAdminUser,)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    # permission_classes = (IsAdminUser,)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.select_related("_type")
    # permission_classes = (IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TrainSerializer
        return TrainListSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer
    permission_classes = (IsAdminUser,)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    # permission_classes = (IsAdminUser,)

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        if self.action == "retrieve":
            return RouteRetrieveSerializer
        return self.serializer_class

    def get_queryset(self):
        if self.action in ["list", "retrieve"]:
            return Route.objects.select_related(
                "source", "destination"
            ).prefetch_related("route_stations")
        return self.queryset


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer


class RouteJourneysViewSet(viewsets.ModelViewSet):
    # serializer_class = RouteJourneysListSerializer

    def get_queryset(self):
        route_id = self.kwargs["route_id"]
        return (
            Journey.objects.filter(route__id=route_id)
            .select_related("train")
            .prefetch_related(
                "crew", "journey_stations__route_station__station"
            )
        )

    def get_object(self):
        queryset = self.get_queryset()
        journey_id = self.kwargs["journey_id"]
        try:
            return queryset.get(id=journey_id)
        except Journey.DoesNotExist:
            raise NotFound("Journey not found for this route.")

    def perform_create(self, serializer):
        route_id = self.kwargs["route_id"]
        serializer.save(route_id=route_id)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteJourneysListSerializer
        return RouteJourneysSerializer


class JourneySearchView(APIView):
    def post(self, request):
        serializer = JourneySearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_departure_station = serializer.validated_data[
            "requested_departure_station"
        ]
        requested_arrival_station = serializer.validated_data[
            "requested_arrival_station"
        ]
        requested_departure_time = serializer.validated_data[
            "requested_departure_time"
        ]

        try:
            from_station = Station.objects.get(
                name=requested_departure_station
            )
            to_station = Station.objects.get(name=requested_arrival_station)
        except Station.DoesNotExist:
            return Response(
                {"detail": "Station not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        journeys = find_journeys_between_stations(
            from_station, to_station, requested_departure_time
        )

        response_data = [
            {
                "journey_id": j.id,
                "route": str(j.route),
                "train": str(j.train),
                "departure_time": dt.strftime("%Y-%m-%d %H:%M"),
            }
            for j, dt in journeys
        ]

        return Response(response_data, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            "tickets",
            "tickets__departure_station",
            "tickets__arrival_station",
            "tickets__journey",
            "tickets__journey__route",
            "tickets__journey__route__route_stations",
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
