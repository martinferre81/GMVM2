# reclamos/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User



class TipoReclamo(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class EstadoReclamo(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Reclamo(models.Model):

    PRIORIDADES = [
        (3, 'Alta'),
        (2, 'Media'),
        (1, 'Baja'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reclamos_creados')
    usuario_ult_modificacion = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='reclamos_modificados')

    id_contribuyente = models.IntegerField()

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()

    tipo_reclamo = models.ForeignKey(
        TipoReclamo,
        on_delete=models.PROTECT
    )

    estado = models.ForeignKey(
        EstadoReclamo,
        on_delete=models.PROTECT
    )

    prioridad = models.IntegerField(choices=PRIORIDADES, default=1)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)


    def save(self, *args, **kwargs):
        if self.estado.nombre.lower() == "finalizado" and not self.fecha_cierre:
            self.fecha_cierre = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reclamo #{self.id} - {self.id_contribuyente}"

class HistorialReclamo(models.Model):
        reclamo = models.ForeignKey(
            Reclamo,
            on_delete=models.CASCADE,
            related_name='historial'
        )

        usuario = models.ForeignKey(
            User,
            on_delete=models.SET_NULL,
            null=True
        )

        accion = models.CharField(max_length=100)

        estado_anterior = models.ForeignKey(
            EstadoReclamo,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='estado_anterior'
        )

        estado_nuevo = models.ForeignKey(
            EstadoReclamo,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='estado_nuevo'
        )

        tipo_anterior = models.ForeignKey(
            TipoReclamo,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='tipo_anterior'
        )

        tipo_nuevo = models.ForeignKey(
            TipoReclamo,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='tipo_nuevo'
        )

        prioridad_anterior = models.IntegerField(null=True, blank=True)
        prioridad_nueva = models.IntegerField(null=True, blank=True)

        titulo_anterior = models.CharField(max_length=200, null=True, blank=True)
        titulo_nuevo = models.CharField(max_length=200, null=True, blank=True)

        descripcion_anterior = models.TextField(null=True, blank=True)
        descripcion_nueva = models.TextField(null=True, blank=True)

        vecino_anterior = models.IntegerField(null=True, blank=True)
        vecino_nuevo = models.IntegerField(null=True, blank=True)

        fecha = models.DateTimeField(auto_now_add=True)

        comentario = models.TextField(blank=True)

        def __str__(self):
            return f"Historial Reclamo {self.reclamo.id} - {self.accion}"
