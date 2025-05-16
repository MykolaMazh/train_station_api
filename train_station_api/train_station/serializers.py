from rest_framework import serializers, generics
from rest_framework.relations import PrimaryKeyRelatedField

from .models import (
    Journey,
    CrewMember,
    Station,
    Train,
    TrainType,
    Route,
    RouteStation,
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
        print(route_stations_data)
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
                f"Departs at {j.departure_time.strftime("%H:%M")} - Arrives at {j.arrival_time.strftime("%H:%M")}"
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


class RouteJourneysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = [
            "id",
            "route_journey_number",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "no_journey_month_days",
            "no_journey_week_days",
        ]


class RouteJourneysListSerializer(serializers.ModelSerializer):
    train = serializers.StringRelatedField()
    crew = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = [
            "id",
            "route_journey_number",
            "train",
            "crew",
            "departure_time",
            "arrival_time",
            "no_journey_month_days",
            "no_journey_week_days",
        ]

    def get_crew(self, obj):
        return [str(crew_m) for crew_m in obj.crew.all()]


class JourneySearchSerializer(serializers.Serializer):
    requested_departure_station = serializers.CharField()
    requested_arrival_station = serializers.CharField()
    requested_departure_time = serializers.DateTimeField()
