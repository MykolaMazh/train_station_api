from datetime import datetime

from django.db.models import Q
from django.utils.timezone import make_aware, is_naive

from train_station.models import Journey, Station, Route


def find_journeys_between_stations(from_station, to_station, date_time):
    journey_date = date_time.date()

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
        .select_related(
            "route", "train", "route__source", "route__destination"
        )
        .prefetch_related(
            "route__route_stations__station", "route__route_stations"
        )
        .distinct()
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

        if from_station_number >= to_station_number:
            continue

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

        if is_naive(departure_dt):
            departure_dt = make_aware(departure_dt)

        if departure_dt >= date_time:
            matching_journeys.append((journey, departure_dt))

    return matching_journeys
