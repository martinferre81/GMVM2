from django.contrib import admin

from django.contrib import admin
from .models import Reclamo, TipoReclamo, EstadoReclamo, HistorialReclamo, Contribuyente, ReclamoFoto

admin.site.register(Reclamo)
admin.site.register(TipoReclamo)
admin.site.register(EstadoReclamo)
admin.site.register(HistorialReclamo)
admin.site.register(Contribuyente)
admin.site.register(ReclamoFoto)


