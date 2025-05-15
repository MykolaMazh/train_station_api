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
    JourneyStation,
RouteStation
)


class JourneyStationIncluded(admin.StackedInline):
    model = JourneyStation
    extra = 0

class RouteStationIncluded(admin.StackedInline):
    model = RouteStation
    extra = 0


class JourneyAdmin(admin.ModelAdmin):
    inlines = [JourneyStationIncluded]
    # list_display = ["route"]


class JourneyIncluded(admin.StackedInline):
    save_as = True
    list_display = ["route", "departure_time", "arrival_time"]
    ordering = ["departure_time"]
    model = Journey
    extra = 0


class TicketAdmin(admin.ModelAdmin):
    save_as = True


class RouteAdmin(admin.ModelAdmin):
    inlines = [RouteStationIncluded, JourneyIncluded]


admin.site.register(Train)
# admin.site.register(Journey, JourneyAdmin)
admin.site.register(Journey, JourneyAdmin)
admin.site.register(CrewMember)
admin.site.register(TrainType)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Station)
admin.site.register(Order)
admin.site.register(Route, RouteAdmin)
# admin.site.register(IntermediateStation)
