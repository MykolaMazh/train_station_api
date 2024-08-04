from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
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
    start_route_station = models.ForeignKey(
        "Station",
        on_delete=models.CASCADE,
        related_name="start_station_routes",
    )
    end_route_station = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="start_station_ends"
    )
    source = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="source_routes"
    )
    destination = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="destination_routes"
    )
    distance = models.PositiveIntegerField(
        validators=[MaxValueValidator(settings.MAX_ROUTE_DISTANCE)]
    )

    def __str__(self):
        return f"{self.source} - {self.destination}"


class Ticket(models.Model):
    car = models.PositiveSmallIntegerField()
    seat = models.PositiveSmallIntegerField()
    journey = models.ForeignKey(Journey, on_delete=models.DO_NOTHING)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.journey} /// car:{self.car} seat:{self.seat}"

    def clean(self):
        journey = self.journey

        current_journeys = Journey.objects.filter(
            train=journey.train,
            departure_time__lte=journey.departure_time,
            arrival_time__gt=journey.departure_time,
        )
        for cur_j in current_journeys:
            for ticket in cur_j.ticket_set.all():
                if ticket.car == self.car:
                    if ticket.seat == self.seat:
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
