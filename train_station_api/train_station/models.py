from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Journey(models.Model):
    route = models.ForeignKey(
        "Route", related_name="journeys", on_delete=models.CASCADE
    )
    train = models.ForeignKey(
        "Train", related_name="journeys", on_delete=models.SET_NULL, null=True
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField("CrewMember", related_name="journeys")

    def __str__(self):
        return f"{self.route} - ({self.departure_time})"


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
        return f"{self.departure_station} - {self.arrival_station} /// car:{self.car} seat:{self.seat} /// {self.journey}"

    def clean(self):

        same_seat_querry = self.journey.ticket_set.filter(
            car=self.car, seat=self.seat
        )
        if same_seat_querry:
            tickets = {}

            def get_source_number(ticket):
                return (
                    self.journey.journey_intermediate_stations.get(
                        name=ticket.departure_station
                    ).route_ordinal_station_number
                    if ticket.departure_station != self.journey.route.source
                    else 0
                )

            def get_destination_number(ticket):
                return (
                    self.journey.journey_intermediate_stations.get(
                        name=ticket.arrival_station
                    ).route_ordinal_station_number
                    if ticket.arrival_station != self.journey.route.destination
                    else 1000
                )

            try:
                requested_source = get_source_number(self)
                requested_destination = get_destination_number(self)
                for ticket in same_seat_querry:
                    tickets.update(
                        {
                            ticket: {
                                "sorce_number": get_source_number(ticket),
                                "destination_number": get_destination_number(
                                    ticket
                                ),
                            }
                        }
                    )

                for ticket in tickets:
                    if (
                        ticket.departure_station == self.journey.route.source
                        and ticket.arrival_station
                        == self.journey.route.destination
                    ) or (
                        requested_source < get_destination_number(ticket)
                        and requested_destination > get_source_number(ticket)
                    ):
                        raise ValidationError("The seat is not available")
            except ObjectDoesNotExist:
                raise ValidationError(
                    "You cannot reach the desired station by this train."
                )

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

    arrival = models.DateTimeField()
    departure = models.DateTimeField()
    route_distance_already_passed_km = models.SmallIntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="journey_intermediate_stations",
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
