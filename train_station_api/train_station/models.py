import datetime

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.conf import settings


class Journey(models.Model):
    route = models.ForeignKey(
        "Route", related_name="journeys", on_delete=models.CASCADE
    )
    train = models.ForeignKey(
        "Train", related_name="journeys", on_delete=models.SET_NULL, null=True
    )
    crew = models.ManyToManyField("CrewMember", related_name="journeys")
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    no_journey_month_days = models.JSONField(
        help_text="list of days. Example [12, 18, 31]",
        null=True,
        blank=True,
    )
    no_journey_week_days = models.JSONField(
        help_text="list of week days. Example [0, 4]",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.route} /{self.departure_time.strftime('%H:%M')}/"

    class Meta:
        ordering = ["departure_time"]


class CrewMember(models.Model):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Route(models.Model):
    source = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="source_routes"
    )
    destination = models.ForeignKey(
        "Station",
        on_delete=models.CASCADE,
        related_name="destination_routes",
    )
    distance = models.PositiveIntegerField(
        validators=[MaxValueValidator(settings.MAX_ROUTE_DISTANCE)]
    )

    def __str__(self):
        return f"{self.source} - {self.destination}"

    @property
    def route_station_numbers(self):
        return {
            route_station.id: index
            for index, route_station in enumerate(
                self.route_stations.order_by(
                    "route_distance_already_passed_km"
                ),
                start=1,
            )
        }


class Ticket(models.Model):
    departure_station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="departure_tickets"
    )
    arrival_station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="arrival_tickets"
    )
    journey_date = models.DateField()
    car = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    seat = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    journey = models.ForeignKey(
        Journey, on_delete=models.DO_NOTHING, related_name="tickets"
    )
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="tickets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    computed_departure_datetime = models.DateTimeField(null=True, blank=True)
    computed_arrival_datetime = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"{self.departure_station} - {self.arrival_station}"
            f" /// car:{self.car} seat:{self.seat}"
            f" /// {self.journey}"
        )

    @property
    def arrival_datetime(self):
        arrival_journey_station = self.journey.journey_stations.filter(
            route_station__station=self.arrival_station
        ).first()
        if arrival_journey_station:
            if (
                arrival_journey_station.arrival_time
                >= self.departure_datetime.time()
            ):
                return datetime.datetime.combine(
                    self.journey_date, arrival_journey_station.arrival_time
                )
            return datetime.datetime.combine(
                self.journey_date + datetime.timedelta(days=1),
                arrival_journey_station.arrival_time,
            )

        else:
            if self.journey.arrival_time >= self.departure_datetime.time():
                return datetime.datetime.combine(
                    self.journey_date, self.journey.arrival_time
                )
            return datetime.datetime.combine(
                self.journey_date + datetime.timedelta(days=1),
                self.journey.arrival_time,
            )

    @property
    def departure_datetime(self):
        departure_journey_station = self.journey.journey_stations.filter(
            route_station__station=self.departure_station
        ).first()
        if departure_journey_station:
            return datetime.datetime.combine(
                self.journey_date, departure_journey_station.departure_time
            )
        return datetime.datetime.combine(
            self.journey_date, self.journey.departure_time
        )

    def clean(self):
        journey_day = self.journey_date.day
        journey_weekday = self.journey_date.weekday()

        if (
            self.journey.no_journey_month_days
            and journey_day in self.journey.no_journey_month_days
        ):
            raise ValidationError(
                f"Journey does not operate on day {journey_day} of the month."
            )

        if (
            self.journey.no_journey_week_days
            and journey_weekday in self.journey.no_journey_week_days
        ):
            raise ValidationError(
                f"Journey does not operate on weekday {journey_weekday}."
            )

        requested_departure_station_number = Station.get_station_number(
            self.departure_station, self.journey.route
        )
        requested_arrival_station_number = Station.get_station_number(
            self.arrival_station, self.journey.route
        )

        if (
            requested_arrival_station_number
            <= requested_departure_station_number
        ):
            raise ValidationError("Invalid connection for this route.")

        same_seat_querry = self.journey.tickets.filter(
            car=self.car,
            seat=self.seat,
            journey_date__gte=self.journey_date - datetime.timedelta(days=1),
            journey_date__lt=self.journey_date + datetime.timedelta(days=1),
        )

        if same_seat_querry:
            for ticket in same_seat_querry:
                if (
                    ticket.departure_datetime
                    <= self.departure_datetime
                    < ticket.arrival_datetime
                ) or (
                    ticket.departure_datetime
                    < self.arrival_datetime
                    <= ticket.arrival_datetime
                ):
                    raise ValidationError("The seat is not available")

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.computed_departure_datetime = self.departure_datetime
        self.computed_arrival_datetime = self.arrival_datetime
        self.full_clean()  # Calls the clean method before saving
        return super().save(force_insert, force_update, using, update_fields)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.id} - {self.created_at}"


class Station(models.Model):
    name = models.CharField(max_length=150, unique=True)
    longitude = models.FloatField(
        validators=[MaxValueValidator(90), MinValueValidator(-90)]
    )
    latitude = models.FloatField(
        validators=[MaxValueValidator(180), MinValueValidator(-180)]
    )

    class Meta:
        ordering = ["name"]

    @staticmethod
    def get_station_number(station: "Station", route: Route):
        if station == route.source:
            return 0
        if station == route.destination:
            return 1000

        route_station = route.route_stations.filter(
            station_id=station.id
        ).first()
        if route_station is None:
            raise ValueError(f"Station {station} not in route {route}")
        return route.route_station_numbers.get(route_station.id)

    def __str__(self):
        return self.name


class RouteStation(models.Model):
    """Defines stations along a route, independent of specific journeys."""

    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="route_stations"
    )
    station = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="route_stations"
    )
    route_distance_already_passed_km = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("route", "station")  # Prevents duplicates

    def __str__(self):
        return f"{self.station.name} on {self.route}"


class JourneyStation(models.Model):
    """Maps stations to specific journeys with arrival and departure times."""

    journey = models.ForeignKey(
        Journey, on_delete=models.CASCADE, related_name="journey_stations"
    )
    route_station = models.ForeignKey(
        RouteStation, on_delete=models.CASCADE, related_name="journey_stations"
    )

    arrival_time = models.TimeField(null=True, blank=True)
    departure_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ("journey", "route_station")  # Prevents duplicates

    def __str__(self):
        return f"{self.route_station.station.name} ({self.journey})"


class Train(models.Model):
    name = models.CharField(max_length=100, unique=True)
    car_num = models.PositiveSmallIntegerField()
    places_in_car = models.PositiveSmallIntegerField()
    _type = models.ForeignKey("TrainType", on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.name} - capacity:{self.places_in_car}"


class TrainType(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name
