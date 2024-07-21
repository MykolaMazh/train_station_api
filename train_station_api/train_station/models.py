from django.conf import settings
from django.contrib.auth.models import User, AbstractUser
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


class CrewMember(models.Model):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)


class Route(models.Model):
    source = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="source_routes"
    )
    destination = models.ForeignKey(
        "Station", on_delete=models.CASCADE, related_name="destination_routes"
    )
    distance = models.PositiveIntegerField(
        validators=[MaxValueValidator(settings.MAX_ROUTE_DISTANCE)]
    )


class Ticket(models.Model):
    cargo = models.PositiveIntegerField(default=settings.CARGO)
    seat_quantity = models.PositiveSmallIntegerField()
    journey = models.ForeignKey(Journey, on_delete=models.DO_NOTHING)
    order = models.ForeignKey("Order", on_delete=models.CASCADE)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Station(models.Model):
    name = models.CharField(max_length=150)
    longitude = models.FloatField(
        validators=[MaxValueValidator(90), MinValueValidator(-90)]
    )
    latitude = models.FloatField(
        validators=[MaxValueValidator(180), MinValueValidator(-180)]
    )


class Train(models.Model):
    name = models.CharField(max_length=100)
    corgo_num = models.PositiveIntegerField()
    places_in_cargo = models.PositiveIntegerField()
    _type = models.ForeignKey("TrainType", on_delete=models.DO_NOTHING)


class TrainType(models.Model):
    name = models.CharField(max_length=150)
