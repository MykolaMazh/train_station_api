from typing import List

from django.db.models import Q
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
    OpenApiTypes,
)
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView

from train_station.models import (
    Journey,
    CrewMember,
    Station,
    Train,
    TrainType,
    Route,
    Order,
    Ticket,
)
from train_station.permissions import IsAdminOrReadOnly
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
    SearchAvailableSeatsSerializer,
)
from train_station.utils import find_journeys_between_stations


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer
    permission_classes = (IsAdminUser,)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminUser,)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.select_related("_type")
    permission_classes = (IsAdminUser,)

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
    permission_classes = (IsAdminOrReadOnly,)

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
    permission_classes = (IsAdminOrReadOnly,)


class RouteJourneysViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminOrReadOnly,)

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

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RouteJourneysListSerializer
        return RouteJourneysSerializer

    @extend_schema(
        summary="Get all journey of the route",
        responses={
            200: OpenApiResponse(
                response=RouteJourneysListSerializer(many=True),
                description="A list of journeys for the given route",
                examples=[
                    OpenApiExample(
                        name="Example list of route journeys",
                        value=(
                            {
                                "id": 2,
                                "train": "TLK2135 - capacity:35",
                                "crew": ["Teo Hernandes", "Jonatan Taa"],
                                "departure_time": "09:00",
                                "arrival_time": "16:00",
                                "no_journey_month_days": [3],
                                "no_journey_week_days": [3],
                                "journey_stations": [
                                    "Korosten",
                                    "Shepetivka",
                                    "Ternopil",
                                ],
                            },
                            {
                                "id": 3,
                                "train": "TLK2031 - capacity:31",
                                "crew": ["Jadon Sanho", "Liam Delap"],
                                "departure_time": "22:00",
                                "arrival_time": "05:00",
                                "no_journey_month_days": [7],
                                "no_journey_week_days": [],
                                "journey_stations": ["Shepetivka", "Ternopil"],
                            },
                        ),
                        description="An example journey response",
                    )
                ],
            )
        },
    )
    def list(self, request, *args, **kwargs):
        """

        Returns a list of journeys with their associated data.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new Journey",
        description="This endpoint allows you to create a new journey"
        " with its associated route, train, crew,"
        " and schedule details.",
        request=RouteJourneysSerializer(),
        examples=[
            OpenApiExample(
                "Successful Journey Creation Request",
                summary="Example request for creating a journey.",
                description="Journey is been created with route_id=route_id",
                value={
                    "train": 3,
                    "crew": [1, 2],
                    "departure_time": "07:00",
                    "arrival_time": "12:30",
                    "no_journey_month_days": [2],
                    "no_journey_week_days": [0, 3],
                    "journey_stations": [
                        {
                            "route_station": 1,
                            "arrival_time": "08:30",
                            "departure_time": "08:32",
                        }
                    ],
                },
                request_only=True,  # This example is only for the request body
            )
        ],
        responses={
            201: OpenApiResponse(
                response=RouteJourneysListSerializer(),
                description="Created journey for the given route",
                examples=[
                    OpenApiExample(
                        name="Example list of route journeys",
                        value={
                            "id": 11,
                            "train": 3,
                            "crew": [1, 2],
                            "departure_time": "07:00",
                            "arrival_time": "12:30",
                            "no_journey_month_days": [2],
                            "no_journey_week_days": [0, 3],
                            "journey_stations": [
                                {
                                    "route_station": 1,
                                    "arrival_time": "08:30",
                                    "departure_time": "08:32",
                                }
                            ],
                        },
                        description="An example journey response",
                    )
                ],
            )
        },
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        route_id = self.kwargs["route_id"]
        serializer.save(route_id=route_id)

    @extend_schema(
        summary="Get the journey of the route",
        responses={
            200: OpenApiResponse(
                response=RouteJourneysListSerializer(),
                description="A journeys with journey_id of the given route",
            )
        },
    )
    def retrieve(self, request, *args, **kwargs):
        "A journeys with journey_id of the given route"
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update the journey of the route",
        description="This endpoint allows you to update"
        " the journey of the route",
        request=RouteJourneysSerializer(),
        examples=[
            OpenApiExample(
                "Successful Journey updation Request",
                summary="Example request for updating the journey.",
                description="Journey with route_id and journey_id"
                " is been updated",
                value={
                    "train": 3,
                    "crew": [1, 2],
                    "departure_time": "07:00",
                    "arrival_time": "12:30",
                    "no_journey_month_days": [2],
                    "no_journey_week_days": [0, 3],
                    "journey_stations": [
                        {
                            "route_station": 1,
                            "arrival_time": "08:30",
                            "departure_time": "08:42",
                        }
                    ],
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=RouteJourneysListSerializer(),
                description="Updated journey for the given route",
                examples=[
                    OpenApiExample(
                        name="Example journey updated",
                        value={
                            "id": 9,
                            "train": 3,
                            "crew": [1, 2],
                            "departure_time": "07:00",
                            "arrival_time": "12:30",
                            "no_journey_month_days": [2],
                            "no_journey_week_days": [0, 3],
                            "journey_stations": [
                                {
                                    "route_station": 1,
                                    "arrival_time": "08:30",
                                    "departure_time": "08:42",
                                }
                            ],
                        },
                        description="An example journey updatedresponse",
                    )
                ],
            )
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially Update the journey of the route",
        description="This endpoint allows you to update some "
        "fields of the journey of the route",
        request=RouteJourneysSerializer(),
        examples=[
            OpenApiExample(
                "Successful Journey updation Request",
                summary="Example request for updating the journey.",
                description="Journey with route_id and journey_id"
                " is been updated",
                value={
                    "train": 4,
                    "crew": [1, 3],
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=RouteJourneysListSerializer(),
                description="Updated journey for the given route",
                examples=[
                    OpenApiExample(
                        name="Example journey updated",
                        value={
                            "id": 9,
                            "train": 4,
                            "crew": [1, 3],
                            "departure_time": "07:00",
                            "arrival_time": "12:30",
                            "no_journey_month_days": [2],
                            "no_journey_week_days": [0, 3],
                            "journey_stations": [
                                {
                                    "route_station": 1,
                                    "arrival_time": "08:30",
                                    "departure_time": "08:42",
                                }
                            ],
                        },
                        description="An example journey updatedresponse",
                    )
                ],
            )
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete the journey of the route",
        description="This endpoint allows you to delete journey"
        " with journey_id of the route with route_id",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class JourneySearchView(APIView):

    @extend_schema(
        summary="Searching for journeys between stations",
        description="This endpoint allows you to find a journey"
        " according to the requirements",
        request=JourneySearchSerializer(),
        examples=[
            OpenApiExample(
                name="Example request",
                description="Search for journey using station names",
                value={
                    "requested_departure_station": "Kyiv",
                    "requested_arrival_station": "Ternopil",
                    "requested_departure_time": "2025-06-08T01:01",
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=List[OpenApiTypes.OBJECT],
                description="Response of found journeys",
                examples=[
                    OpenApiExample(
                        name="Example list of route journeys",
                        value=[
                            {
                                "journey_id": 2,
                                "route": "Kyiv - Lviv",
                                "train": "TLK2135 - capacity:35",
                                "departure_datetime": "2025-06-08 09:00",
                                "arrival_datetime": "2025-06-08 14:30",
                            },
                            {
                                "journey_id": 3,
                                "route": "Kyiv - Lviv",
                                "train": "TLK2031 - capacity:31",
                                "departure_datetime": "2025-06-08 22:00",
                                "arrival_datetime": "2025-06-09 03:00",
                            },
                        ],
                        description="list of journeys",
                    )
                ],
            )
        },
    )
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
                "departure_datetime": dt.strftime("%Y-%m-%d %H:%M"),
                "arrival_datetime": at.strftime("%Y-%m-%d %H:%M"),
            }
            for j, dt, at in journeys
        ]

        response_data_sorted = sorted(
            response_data, key=lambda x: x["departure_datetime"]
        )

        return Response(response_data_sorted, status=status.HTTP_200_OK)


class TicketsAvailableView(APIView):

    @extend_schema(
        summary="Find available seats",
        description="This endpoint allows you to find available seats for "
        "the journey according to the deparure and arrival time",
        request=SearchAvailableSeatsSerializer(),
        examples=[
            OpenApiExample(
                name="Example search available seats",
                description="Search for available seats, using journey_id,"
                " departure_time, arrival_time "
                "got from 'api/v1/train_station/search-journeys/'"
                "(Searching for journeys between stations)",
                value={
                    "journey_id": 2,
                    "departure_datetime": "2025-06-06T08:30",
                    "arrival_datetime": "2025-06-06T12:45:00Z",
                },
                request_only=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Response of available seats for the journey",
                examples=[
                    OpenApiExample(
                        name="Example of available seats",
                        value={
                            "1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            "2": [1, 4, 5, 6, 7, 8, 9, 10],
                        },
                        description="Response of available seats"
                        " for the journey in format"
                        " {'car namber':[list of available seats in car]}",
                    )
                ],
            )
        },
    )
    def post(self, request):
        serializer = SearchAvailableSeatsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        journey_id = serializer.validated_data["journey_id"]
        arrival_datetime = serializer.validated_data["arrival_datetime"]
        departure_datetime = serializer.validated_data["departure_datetime"]

        journey = get_object_or_404(
            Journey.objects.select_related("train"), pk=journey_id
        )

        tickets_bought = (
            Ticket.objects.filter(journey=journey_id)
            .filter(
                Q(
                    computed_arrival_datetime__gte=departure_datetime,
                    computed_arrival_datetime__lte=arrival_datetime,
                )
                | Q(
                    computed_departure_datetime__gte=departure_datetime,
                    computed_departure_datetime__lte=arrival_datetime,
                )
            )
            .values("car", "seat")
        )

        seats_occupied = {}
        for car_seat in tickets_bought:  # {"car": 2, "seat": 2}
            seats_occupied.setdefault(car_seat["car"], []).append(
                car_seat["seat"]
            )

        cars_number = journey.train.car_num
        seats_number = journey.train.places_in_car
        all_seats = {
            car: [seat for seat in range(1, seats_number + 1)]
            for car in range(1, cars_number + 1)
        }

        seats_available = {
            car: [
                seat
                for seat in all_seats[car]
                if seat not in seats_occupied.get(car, [])
            ]
            for car in all_seats
        }

        return Response(seats_available, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

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
