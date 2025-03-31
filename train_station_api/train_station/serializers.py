from rest_framework import serializers

from .models import Journey, CrewMember, Station, Train, TrainType


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

    # class Meta(TrainListSerializer.Meta):
    #     fields = TrainListSerializer.Meta.fields

    # class Meta:
    #     model = Train
    #     fields = ["id", "name", "car_num", "places_in_car", "type"]




class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = "__all__"



