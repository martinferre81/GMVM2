from django.contrib import admin

from django.contrib import admin
from .models import Reclamo, TipoReclamo, EstadoReclamo, HistorialReclamo

# Registrar modelos para que aparezcan en el admin
admin.site.register(Reclamo)
admin.site.register(TipoReclamo)
admin.site.register(EstadoReclamo)
admin.site.register(HistorialReclamo)


