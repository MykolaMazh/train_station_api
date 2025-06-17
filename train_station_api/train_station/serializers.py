from django.db import transaction
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import (
    Journey,
    CrewMember,
    Station,
    Train,
    TrainType,
    Route,
    RouteStation,
    JourneyStation,
    Ticket,
    Order,
)


class CrewMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrewMember
        fields = ["id", "first_name", "last_name"]


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["id", "name", "longitude", "latitude"]


class TrainListSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="_type")

    class Meta:
        model = Train
        fields = ["id", "name", "car_num", "places_in_car", "type"]


class TrainSerializer(TrainListSerializer):
    type = serializers.PrimaryKeyRelatedField(
        queryset=TrainType.objects.all(), source="_type"
    )


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ["id", "name"]


class RouteStationSerializer(serializers.ModelSerializer):

    class Meta:
        model = RouteStation
        fields = [
            "id",
            "station",
            "route_ordinal_station_number",
            "route_distance_already_passed_km",
        ]


class RouteStationListSerializer(RouteStationSerializer):
    station = serializers.CharField()


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = "__all__"


class RouteSerializer(serializers.ModelSerializer):
    route_stations = RouteStationSerializer(many=True)

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance", "route_stations"]

    def create(self, validated_data):
        route_stations_data = validated_data.pop("route_stations")
        route = Route.objects.create(**validated_data)
        for route_station in route_stations_data:
            RouteStation.objects.create(route=route, **route_station)
        return route

    def update(self, instance, validated_data):
        route_stations_data = validated_data.pop("route_stations", None)

        # Update the Route fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if route_stations_data is not None:
            # Clear and recreate route stations
            instance.route_stations.all().delete()
            for station_data in route_stations_data:
                RouteStation.objects.create(route=instance, **station_data)

        return instance


class RouteRetrieveSerializer(serializers.ModelSerializer):
    source = StationSerializer()
    destination = StationSerializer()
    route_stations = RouteStationListSerializer(many=True)
    journeys = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            "id",
            "source",
            "destination",
            "distance",
            "route_stations",
            "journeys",
        ]

    def get_journeys(self, obj):
        journeys = obj.journeys.all().order_by("departure_time")
        return [
            (
                f"Departs at {j.departure_time.strftime("%H:%M")} "
                f"- Arrives at {j.arrival_time.strftime("%H:%M")}"
            )
            for j in journeys
        ]


class RouteListSerializer(serializers.ModelSerializer):
    route_stations = serializers.SerializerMethodField()
    source = serializers.CharField()
    destination = serializers.CharField()
    journeys = serializers.IntegerField(
        source="journeys.count", read_only=True
    )

    class Meta:
        model = Route
        fields = [
            "id",
            "source",
            "destination",
            "distance",
            "route_stations",
            "journeys",
        ]

    def get_route_stations(self, obj):
        route_stations = obj.route_stations.select_related("station").order_by(
            "route_ordinal_station_number"
        )
        return [rs.station.name for rs in route_stations]


class JourneyStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = JourneyStation
        fields = ["route_station", "arrival_time", "departure_time"]


class RouteJourneysSerializer(serializers.ModelSerializer):
    journey_stations = JourneyStationSerializer(many=True)

    class Meta:
        model = Journey
        fields = [
            "id",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "no_journey_month_days",
            "no_journey_week_days",
            "journey_stations",
        ]

    def create(self, validated_data):
        journey_stations_data = validated_data.pop("journey_stations")
        crew_data = validated_data.pop("crew", None)
        journey = Journey.objects.create(**validated_data)
        if crew_data is not None:
            journey.crew.set(crew_data)
        for journey_station in journey_stations_data:
            JourneyStation.objects.create(journey=journey, **journey_station)
        return journey

    def update(self, instance, validated_data):
        journey_stations_data = validated_data.pop("journey_stations", None)
        crew_data = validated_data.pop("crew", None)

        if crew_data is not None:
            instance.crew.set(crew_data)

        # Update the Route fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if journey_stations_data is not None:
            # Clear and recreate route stations
            instance.journey_stations.all().delete()
            for station_data in journey_stations_data:
                JourneyStation.objects.create(journey=instance, **station_data)

        return instance


class RouteJourneysListSerializer(serializers.ModelSerializer):
    train = serializers.StringRelatedField()
    crew = serializers.SerializerMethodField()
    journey_stations = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = [
            "id",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "no_journey_month_days",
            "no_journey_week_days",
            "journey_stations",
        ]

    def get_crew(self, obj):
        return [str(crew_m) for crew_m in obj.crew.all()]

    def get_journey_stations(self, obj):
        return [
            (
                f"{str(station.route_station.station)},"
                f" {station.arrival_time.strftime("%H:%M")}"
                f"-{station.departure_time.strftime("%H:%M")}"
            )
            for station in obj.journey_stations.all()
        ]


class JourneySearchSerializer(serializers.Serializer):
    requested_departure_station = serializers.CharField()
    requested_arrival_station = serializers.CharField()
    requested_departure_time = serializers.DateTimeField()


class SearchAvailableSeatsSerializer(serializers.Serializer):
    journey_id = serializers.IntegerField()
    departure_datetime = serializers.DateTimeField()
    arrival_datetime = serializers.DateTimeField()

    def validate(self, data):
        if data["arrival_datetime"] <= data["departure_datetime"]:
            raise serializers.ValidationError(
                "Arrival must be after departure."
            )
        return data


class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = [
            "id",
            "departure_station",
            "arrival_station",
            "journey_date",
            "car",
            "seat",
            "journey",
        ]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "user", "tickets", "created_at"]
        read_only_fields = ["user", "created_at"]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                ticket = Ticket(order=order, **ticket_data)
                try:
                    ticket.full_clean()  # Call model-level validation
                except DjangoValidationError as e:
                    raise DRFValidationError(e.messages)
                ticket.save()
            return order

    def update(self, instance, validated_data):
        tickets_data = validated_data.pop("tickets", None)

        # Update the Route fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tickets_data is not None:
            # Clear and recreate route stations
            instance.tickets.all().delete()
            for ticket_data in tickets_data:
                Ticket.objects.create(order=instance, **ticket_data)

        return instance
