from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from .models import Journey, CrewMember, Station, Train, TrainType, Route, IntermediateStation


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
    type = serializers.PrimaryKeyRelatedField(queryset=TrainType.objects.all(), source="_type")


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ["id", "name"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteRetrieveSerializer(RouteSerializer):
    source = StationSerializer()
    destination = StationSerializer()

class IntermediateStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntermediateStation
        fields = ["id", "name", "departure_list", "arrival_list"]

class RouteRetrieveSerializer(serializers.ModelSerializer):
    source = StationSerializer()
    destination = StationSerializer()
    intermediate_stations = IntermediateStationSerializer(many=True, source="route_intermediate_stations")

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance", "intermediate_stations"]


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField()
    destination = serializers.CharField()






class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = "__all__"


