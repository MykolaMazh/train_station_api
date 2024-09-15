from django.contrib import admin

from train_station.models import (
    Train,
    Journey,
    CrewMember,
    TrainType,
    Ticket,
    Station,
    Order,
    Route,
    IntermediateStation,
)


class JourneyIncluded(admin.StackedInline):
    save_as = True
    list_display = ["route", "departure_time", "arrival_time"]
    ordering = ["departure_time"]
    model = Journey
    extra = 0


class TicketAdmin(admin.ModelAdmin):
    save_as = True


class IntermediateStationIncluded(admin.StackedInline):
    model = IntermediateStation
    extra = 0


class RouteAdmin(admin.ModelAdmin):
    inlines = [IntermediateStationIncluded, JourneyIncluded]


admin.site.register(Train)
admin.site.register(Journey)
admin.site.register(CrewMember)
admin.site.register(TrainType)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Station)
admin.site.register(Order)
admin.site.register(Route, RouteAdmin)
admin.site.register(IntermediateStation)
