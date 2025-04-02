import datetime, time
import json


from django.core.management.base import BaseCommand
from django.db.models import Q

from train_station.models import Ticket, Journey, Route


class Command(BaseCommand):
    help = "Displays current time"

    def handle(self, **kwargs):
        requested_departure_station = "Kyiv"
        requested_arrival_station = "Rivne"
        requested_departure_time = datetime.datetime.now().time()
        print(requested_departure_time)

        routes = (
            Route.objects.filter(
                Q(source__name=requested_departure_station)
                | Q(
                    route_intermediate_stations__name__name=requested_departure_station
                ),
            )
            .filter(
                Q(
                    route_intermediate_stations__name__name=requested_arrival_station
                )
                | Q(destination__name=requested_arrival_station)
            )
            .distinct()
        )
        found_journeys = {}

        def update_found_journeys(journey, departure_time):
            found_journeys.update({journey: departure_time})

        if routes:
            straight_routes = routes.filter(
                source__name=requested_departure_station
            )

            if straight_routes:
                for route in straight_routes:
                    _routes = route.journeys.all()
                    straight_routes_journeys = _routes.filter(
                        departure_time__gte=requested_departure_time
                    )
                    if straight_routes_journeys:
                        for journey in straight_routes_journeys:
                            update_found_journeys(
                                journey, journey.departure_time
                            )
                    else:
                        for journey in _routes:
                            update_found_journeys(
                                journey, journey.departure_time
                            )

            passing_routes = routes.filter(
                route_intermediate_stations__name__name=requested_departure_station
            )
            if passing_routes:
                for route in passing_routes:
                    departure_time_list_str = (
                        route.route_intermediate_stations.filter(
                            name__name=requested_departure_station
                        ).values_list("departure_list")[0][0]
                    )
                    departure_time_list = json.loads(departure_time_list_str)
                    add_all_journeys = True
                    for index, (hours, seconds) in enumerate(
                        departure_time_list
                    ):
                        departure_time = datetime.time(hours, seconds)
                        if departure_time >= requested_departure_time:
                            current_journey = route.journeys.order_by(
                                "departure_time"
                            )[index]
                            update_found_journeys(
                                current_journey, departure_time
                            )
                            add_all_journeys = False
                    if add_all_journeys:
                        for index, journey in enumerate(
                            route.journeys.order_by("departure_time")
                        ):
                            update_found_journeys(
                                journey,
                                datetime.time(
                                    departure_time_list[index][0],
                                    departure_time_list[index][1],
                                ),
                            )
        print(found_journeys.items())
        for journey, time in found_journeys.items():
            print(journey, time)
