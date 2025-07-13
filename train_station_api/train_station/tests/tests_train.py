import copy
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
    Ticket,
)


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
            {
                "name": "Train3",
                "car_num": 9,
                "places_in_car": 25,
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

        self.route1_5 = {
            "source": 1,
            "destination": 5,
            "distance": 550,
            "route_stations": [
                {
                    "station": 2,
                    "route_distance_already_passed_km": 150,
                },
                {
                    "station": 3,
                    "route_distance_already_passed_km": 280,
                },
                {
                    "station": 4,
                    "route_distance_already_passed_km": 480,
                },
            ],
        }

        self.route1_5_journeys = [
            {
                "route_journey_number": 1,
                "train": 2,
                "crew": [1, 2],
                "departure_time": "07:00",
                "arrival_time": "12:30",
                "no_journey_month_days": [],
                "no_journey_week_days": [],
                "journey_stations": [
                    {
                        "route_station": 1,
                        "arrival_time": "08:30",
                        "departure_time": "08:32",
                    }
                ],
            },
            {
                "route_journey_number": 2,
                "train": 1,
                "crew": [3, 4],
                "departure_time": "09:00",
                "arrival_time": "16:00",
                "no_journey_month_days": [3],
                "no_journey_week_days": [],
                "journey_stations": [
                    {
                        "route_station": 1,
                        "arrival_time": "10:45",
                        "departure_time": "10:47",
                    },
                    {
                        "route_station": 2,
                        "arrival_time": "12:30",
                        "departure_time": "12:35",
                    },
                    {
                        "route_station": 3,
                        "arrival_time": "14:30",
                        "departure_time": "14:35",
                    },
                ],
            },
        ]

        self.route2_7 = {
            "source": 2,
            "destination": 7,
            "distance": 650,
            "route_stations": [
                {
                    "station": 4,
                    "route_distance_already_passed_km": 250,
                },
                {
                    "station": 5,
                    "route_distance_already_passed_km": 380,
                },
                {
                    "station": 6,
                    "route_distance_already_passed_km": 450,
                },
            ],
        }

        self.route2_7_journeys = [
            {
                "route_journey_number": 1,
                "train": 3,
                "crew": [4, 5],
                "departure_time": "22:00",
                "arrival_time": "12:30",
                "no_journey_month_days": [],
                "no_journey_week_days": [],
                "journey_stations": [
                    {
                        "route_station": 1,
                        "arrival_time": "23:12",
                        "departure_time": "23:32",
                    },
                    {
                        "route_station": 2,
                        "arrival_time": "02:30",
                        "departure_time": "02:35",
                    },
                    {
                        "route_station": 3,
                        "arrival_time": "10:30",
                        "departure_time": "10:39",
                    },
                ],
            },
        ]

        self.route_url = reverse("train_station:route-list")

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
        self.assertEqual(Train.objects.count(), 3)

    def test_only_admin_can_create_crew(self):
        crew_response = self.client.post(
            self.crew_url, self.crew_squad[0], "json"
        )
        self.assertEqual(crew_response.status_code, status.HTTP_403_FORBIDDEN)

        self.user_make_admin()
        self.list_post_request(self.crew_url, self.crew_squad)

        self.assertEqual(CrewMember.objects.count(), 6)

    def test_search_journeys(self):

        self.user_make_admin()
        self.list_post_request(self.station_url, self.stations)
        self.list_post_request(self.train_type_url, self.train_types)
        self.list_post_request(self.train_url, self.train_data)
        self.list_post_request(self.crew_url, self.crew_squad)

        for route_data in [self.route1_5, self.route2_7]:
            self.client.post(self.route_url, route_data, "json")
        self.assertEqual(Route.objects.count(), 2)

        route1_5_journeys_url = reverse(
            "train_station:route-journeys-list", kwargs={"route_id": 1}
        )
        route2_7_journeys_url = reverse(
            "train_station:route-journeys-list", kwargs={"route_id": 2}
        )

        self.list_post_request(route1_5_journeys_url, self.route1_5_journeys)
        self.list_post_request(route2_7_journeys_url, self.route2_7_journeys)
        self.assertEqual(Route.objects.get(id=1).journeys.count(), 2)
        self.assertEqual(Route.objects.get(id=2).journeys.count(), 1)

        search_journey_data = {
            "requested_departure_station": "S2",
            "requested_arrival_station": "S4",
            "requested_departure_time": "2025-06-08T1:30",
        }

        search_url = reverse("train_station:search-journeys")
        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)
        response = self.client.post(search_url, search_journey_data, "json")
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            response.data[0]["departure_datetime"], "2025-06-08 10:47"
        )
        self.assertEqual(
            response.data[1]["departure_datetime"], "2025-06-08 22:00"
        )

    def test_no_same_seat_occupy(self):

        self.user_make_admin()
        self.list_post_request(self.station_url, self.stations)
        self.list_post_request(self.train_type_url, self.train_types)
        self.list_post_request(self.train_url, self.train_data)
        self.list_post_request(self.crew_url, self.crew_squad)

        self.client.post(self.route_url, self.route1_5, "json")

        route1_5_journeys_url = reverse(
            "train_station:route-journeys-list", kwargs={"route_id": 1}
        )
        self.list_post_request(route1_5_journeys_url, self.route1_5_journeys)

        self.user.is_staff = False
        self.user.save()
        self.client.force_authenticate(self.user)

        order_url = reverse("train_station:orders-list")

        ticket1_data = {
            "tickets": [
                {
                    "departure_station": 1,
                    "arrival_station": 2,
                    "journey_date": "2025-06-12",
                    "car": 2,
                    "seat": 1,
                    "journey": 2,
                }
            ]
        }

        ticket2_data = copy.deepcopy(ticket1_data)
        ticket2_data["tickets"][0]["arrival_station"] = 3

        ticket3_data = copy.deepcopy(ticket1_data)
        ticket3_data["tickets"][0]["arrival_station"] = 5

        ticket4_data = copy.deepcopy(ticket1_data)
        ticket4_data["tickets"][0]["departure_station"] = 2
        ticket4_data["tickets"][0]["arrival_station"] = 4

        ticket5_data = copy.deepcopy(ticket1_data)
        ticket5_data["tickets"][0]["journey_date"] = "2025-06-13"

        self.client.post(order_url, ticket1_data, "json")

        for ticket_data in [ticket2_data, ticket3_data]:
            response = self.client.post(order_url, ticket_data, "json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("The seat is not available", str(response.data))

        response = self.client.post(order_url, ticket5_data, "json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Ticket.objects.count(), 2)
