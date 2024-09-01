from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Journey(models.Model):
    route = models.ForeignKey(
        "Route", related_name="journeys", on_delete=models.CASCADE
    )
    train = models.ForeignKey(
        "Train", related_name="journeys", on_delete=models.SET_NULL, null=True
    )
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    crew = models.ManyToManyField("CrewMember", related_name="journeys")

    def __str__(self):
        self_select_related = Journey.objects.filter(
            id=self.id
        ).select_related("route")[0]
        return f"{self_select_related.route} - ({self_select_related.departure_time})"


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
    car = models.PositiveSmallIntegerField()
    seat = models.PositiveSmallIntegerField()
    journey = models.ForeignKey(Journey, on_delete=models.DO_NOTHING)
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
                return self.journey.journey_intermediate_stations.get(
                    name=station
                ).route_ordinal_station_number
            elif station == journey_source:
                return 0
            return 1000

        requested_departure_number = get_station_number(self.departure_station)
        requested_arrival_number = get_station_number(self.arrival_station)

        if requested_arrival_number <= requested_departure_number:
            raise ValidationError("Invalid connection for this route.")

        same_seat_querry = self.journey.ticket_set.filter(
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
                    requested_departure_number < end_stations["arrival_number"]
                    or requested_arrival_number
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
    route_ordinal_station_number = models.PositiveSmallIntegerField()
    name = models.ForeignKey(
        Station, related_name="intermediate_stations", on_delete=models.CASCADE
    )

    arrival_list = models.CharField(
        max_length=256,
        help_text="list of all arrivals\nExample [[10, 23], [17,21], [19,13]]",
    )
    departure_list = models.CharField(
        max_length=256,
        help_text="list of all departures\nExample [[10, 23], [17,21], [19,13]]",
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
