from datetime import timedelta, datetime
import json


from django.core.management.base import BaseCommand
from django.db.models import Q

from train_station.models import (
    Ticket,
    Journey,
    Route,
    JourneyStation,
    Station,
)


class Command(BaseCommand):
    help = "Displays current time"

    def handle(self, **kwargs):
        requested_departure_station = "Kyiv"
        requested_arrival_station = "Ternopil"
        requested_departure_time = datetime.now()

        def find_journeys_between_stations(
            from_station, to_station, date_time
        ):
            journey_date = date_time.date()
            time_threshold = date_time.time()

            matching_journeys = []

            journeys = (
                Journey.objects.filter(
                    (
                        Q(route__route_stations__station=from_station)
                        | Q(route__source=from_station)
                    )
                    & (
                        Q(route__route_stations__station=to_station)
                        | Q(route__destination=to_station)
                    )
                )
                .distinct()
                .prefetch_related("journey_stations", "route__route_stations")
            )
            print("journeys before", len(journeys))

            for journey in journeys:
                if (
                    journey.no_journey_month_days
                    and journey_date.day in journey.no_journey_month_days
                ):
                    continue
                if (
                    journey.no_journey_week_days
                    and journey_date.weekday() in journey.no_journey_week_days
                ):
                    continue

                from_station_number = Station.get_station_number(
                    from_station, journey.route
                )
                to_station_number = Station.get_station_number(
                    to_station, journey.route
                )

                # Make sure direction is correct
                if from_station_number >= to_station_number:
                    continue

                # Combine with date to make full datetime\
                if from_station == journey.route.source:
                    departure_dt = datetime.combine(
                        journey_date, journey.departure_time
                    )
                else:
                    departure_dt = datetime.combine(
                        journey_date,
                        journey.journey_stations.get(
                            route_station__station=from_station
                        ).departure_time,
                    )
                print(departure_dt, date_time)

                # Accept only journeys that depart after or at the given datetime
                if departure_dt >= date_time:
                    matching_journeys.append((journey, departure_dt))

            return matching_journeys

        journeys = find_journeys_between_stations(
            Station.objects.get(name=requested_departure_station),
            Station.objects.get(name=requested_arrival_station),
            requested_departure_time,
        )
        print("journeys after", len(journeys))
        for j, dt in journeys:
            print(f"{j} departs at {dt.strftime("%Y-%m-%d %H:%M")}")
