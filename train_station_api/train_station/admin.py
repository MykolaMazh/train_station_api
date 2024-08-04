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


class TicketAdmin(admin.ModelAdmin):
    save_as = True


admin.site.register(Train)
admin.site.register(Journey)
admin.site.register(CrewMember)
admin.site.register(TrainType)
admin.site.register(Ticket, TicketAdmin)
admin.site.register(Station)
admin.site.register(Order)
admin.site.register(Route)
admin.site.register(IntermediateStation)
