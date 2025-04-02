from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Journey(models.Model):
    route = models.ForeignKey(
        "Route", related_name="journeys", on_delete=models.CASCADE
    )
    route_journey_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )
    train = models.ForeignKey(
        "Train", related_name="journeys", on_delete=models.SET_NULL, null=True
    )
    crew = models.ManyToManyField("CrewMember", related_name="journeys")
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    no_journey_month_days = models.CharField(
        max_length=256,
        help_text="list of days. Example [12, 18, 31]",
        null=True,
        blank=True,
    )
    no_journey_week_days = models.CharField(
        max_length=256,
        help_text="list of week days. Example [0, 4]",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.route}{self.departure_time}"

    class Meta:
        ordering = ["route_journey_number"]


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
        self_related = Route.objects.filter(id=self.id).select_related(
            "source", "destination"
        )[0]
        return f"{self_related.source} - {self_related.destination}"


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
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        self_related = Ticket.objects.filter(id=self.id).select_related(
            "departure_station", "arrival_station", "journey"
        )[0]
        return (
            f"{self_related.departure_station} - {self_related.arrival_station}"
            f" /// car:{self.car} seat:{self.seat}"
            f" /// {self_related.journey}"
        )

    def clean(self):
        journey_source = self.journey.route.source
        journey_destination = self.journey.route.destination

        def get_station_number(station):
            if station not in (journey_source, journey_destination):
                return self.journey.route.route_intermediate_stations.get(
                    name=station
                ).route_ordinal_station_number
            elif station == journey_source:
                return 0
            return 1000

        requested_departure_station_number = get_station_number(
            self.departure_station
        )
        requested_arrival_station_number = get_station_number(
            self.arrival_station
        )

        if (
            requested_arrival_station_number
            <= requested_departure_station_number
        ):
            raise ValidationError("Invalid connection for this route.")

        same_seat_querry = self.journey.tickets.filter(
            car=self.car, seat=self.seat
        )
        if same_seat_querry:
            tickets = {}

            for ticket in same_seat_querry:
                tickets.update(
                    {
                        ticket: {
                            "departure_number": get_station_number(
                                ticket.departure_station
                            ),
                            "arrival_number": get_station_number(
                                ticket.arrival_station
                            ),
                        }
                    }
                )

            for ticket, end_stations in tickets.items():
                if (
                    ticket.departure_station == journey_source
                    and ticket.arrival_station == journey_destination
                ) or (
                    requested_departure_station_number
                    < end_stations["arrival_number"]
                    or requested_arrival_station_number
                    > end_stations["arrival_number"]
                ):
                    raise ValidationError("The seat is not available")

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super().save(force_insert, force_update, using, update_fields)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

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

    def __str__(self):
        return self.name


class IntermediateStation(models.Model):
    route_ordinal_station_number = models.PositiveSmallIntegerField(
        help_text="ordinal number from route source",
        validators=[MinValueValidator(1)],
    )
    name = models.ForeignKey(
        Station, related_name="intermediate_stations", on_delete=models.CASCADE
    )

    arrival_list = models.CharField(
        max_length=256,
        help_text="list of all arrivals in format [[journey#1_hours, journey#1_minutes], "
        "[journey#2_hours, journey#2_minutes], [journey#3_hours, journey#3_minutes]]"
        "Example: [[17,21], [19,30], [23,12]",
    )
    departure_list = models.CharField(
        max_length=256,
        help_text="list of all departures in format [[journey#1_hours, journey#1_minutes], "
        "[journey#2_hours, journey#2_minutes], [journey#3_hours, journey#3_minutes]]"
        "Example: [[20,21], [22,30], [2,12]",
    )
    route_distance_already_passed_km = models.SmallIntegerField()
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="route_intermediate_stations",
    )

    def __str__(self):
        return f"{self.name}"


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
