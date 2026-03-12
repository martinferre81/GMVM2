import random
from datetime import datetime, timedelta

from reclamos.models import Reclamo

fecha_inicio = datetime(2026, 1, 1)
fecha_fin = datetime(2026, 3, 11)

dias_rango = (fecha_fin - fecha_inicio).days

reclamos = Reclamo.objects.all()

for r in reclamos:
    nueva_fecha = fecha_inicio + timedelta(days=random.randint(0, dias_rango))
    r.fecha_creacion = nueva_fecha
    r.save(update_fields=["fecha_creacion"])

print(f"✔ {reclamos.count()} reclamos actualizados con fechas aleatorias")