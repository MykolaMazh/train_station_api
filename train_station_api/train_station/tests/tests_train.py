from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware, is_naive
from rest_framework import status
from rest_framework.test import APIClient

from train_station.models import (
    Station,
    TrainType,
    CrewMember,
    Train,
    Route,
    Journey,
)
from train_station.serializers import JourneySearchSerializer


class OrderTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@gmail.com",
            "testpassword123",
        )
        self.client.force_authenticate(self.user)

        self.station_url = reverse("train_station:station-list")

        self.stations = [
            {"name": "S1", "longitude": 1, "latitude": 1},
            {
                "name": "S2",
                "longitude": 2,
                "latitude": 2,
            },
            {
                "name": "S3",
                "longitude": 3,
                "latitude": 3,
            },
            {
                "name": "S4",
                "longitude": 4,
                "latitude": 4,
            },
            {"name": "S5", "longitude": 5, "latitude": 5},
            {"name": "S6", "longitude": 6, "latitude": 6},
            {"name": "S7", "longitude": 7, "latitude": 7},
            {"name": "S8", "longitude": 8, "latitude": 8},
            {"name": "S9", "longitude": 9, "latitude": 9},
            {"name": "S10", "longitude": 10, "latitude": 10},
            {"name": "S11", "longitude": 11, "latitude": 11},
        ]

        self.train_types = [
            {"name": "city"},
            {"name": "intrecity"},
            {"name": "fast"},
        ]

        self.train_type_url = reverse("train_station:train_type-list")
        self.train_url = reverse("train_station:train-list")

        self.train_data = [
            {
                "name": "Train",
                "car_num": 10,
                "places_in_car": 25,
                "type": 1,
            },
            {
                "name": "Train2",
                "car_num": 11,
                "places_in_car": 26,
                "type": 2,
            },
        ]
        self.crew_url = reverse("train_station:crew_member-list")

        self.crew_squad = [
            {"first_name": "Artur", "last_name": "Roberts"},
            {"first_name": "Kevin", "last_name": "De Bruine"},
            {"first_name": "Teo", "last_name": "Hernandes"},
            {"first_name": "Jonatan", "last_name": "Taa"},
            {"first_name": "Jadon", "last_name": "Sanho"},
            {"first_name": "Liam", "last_name": "Delap"},
        ]

    def user_make_admin(self):
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)

    def list_post_request(self, url, data: list[dict]):
        for _ in data:
            self.client.post(url, _, "json")

    def test_only_admin_can_create_stations(self):

        response = self.client.post(self.station_url, self.stations[0], "json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.user_make_admin()
        self.list_post_request(self.station_url, self.stations)

        self.assertEqual(Station.objects.count(), 11)

    def test_only_admin_can_create_train_and_types(self):
        train_type_response = self.client.post(
            self.train_type_url, self.train_types[0], "json"
        )
        train_response = self.client.post(
            self.train_url, self.train_data[0], "json"
        )
        self.assertEqual(
            train_type_response.status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(train_response.status_code, status.HTTP_403_FORBIDDEN)

        self.user_make_admin()
        self.list_post_request(self.train_type_url, self.train_types)
        self.list_post_request(self.train_url, self.train_data)

        self.assertEqual(TrainType.objects.count(), 3)
        self.assertEqual(Train.objects.count(), 2)

    def test_only_admin_can_create_crew(self):
        crew_response = self.client.post(
            self.crew_url, self.crew_squad[0], "json"
        )
        self.assertEqual(crew_response.status_code, status.HTTP_403_FORBIDDEN)

        self.user_make_admin()
        self.list_post_request(self.crew_url, self.crew_squad)

        self.assertEqual(CrewMember.objects.count(), 6)

