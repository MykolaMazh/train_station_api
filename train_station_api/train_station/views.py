from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics, mixins, viewsets

from train_station.models import Journey, CrewMember, Station, Train, TrainType, Route
from train_station.serializers import (
    JourneySerializer,
    CrewMemberSerializer,
    StationSerializer,
    TrainSerializer, TrainListSerializer, TrainTypeSerializer, RouteSerializer, RouteListSerializer,
    RouteRetrieveSerializer,
)


class CrewMemberViewSet(viewsets.ModelViewSet):
    queryset = CrewMember.objects.all()
    serializer_class = CrewMemberSerializer
    # permission_classes = (IsAdminUser,)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminUser,)


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
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


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer

