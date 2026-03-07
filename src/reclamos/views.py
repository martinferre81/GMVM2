from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin  #Esto restringe las vistas si el usuario no tiene sesion
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Reclamo, HistorialReclamo
from .forms import ReclamoForm
from django.http import JsonResponse
from .models import HistorialReclamo
from datetime import datetime
from django.utils import timezone
from .models import EstadoReclamo, TipoReclamo


# Create your views here.

@login_required
def inicio(request):
    user = request.user

    hoy = timezone.now()

    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0)

    if hoy.month == 12:
        siguiente_mes = hoy.replace(year=hoy.year + 1, month=1, day=1)
    else:
        siguiente_mes = hoy.replace(month=hoy.month + 1, day=1)

    # QUERY BASE (todos los reclamos del mes)
    reclamos = Reclamo.objects.select_related(
        'usuario',
        'estado',
        'tipo_reclamo'
    ).filter(
        fecha_creacion__gte=primer_dia_mes,
        fecha_creacion__lt=siguiente_mes
    )

    # Filtro por permisos del usuario
    if not user.groups.filter(name='ADMINISTRADOR').exists():
        grupos_usuario = user.groups.values_list('name', flat=True)

        reclamos = reclamos.filter(
            tipo_reclamo__nombre__in=grupos_usuario
        )
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    vecino = request.GET.get('vecino')
    tipo = request.GET.get('tipo')

    if fecha_desde:
        reclamos = reclamos.filter(fecha_creacion__date__gte=fecha_desde)

    if fecha_hasta:
        reclamos = reclamos.filter(fecha_creacion__date__lte=fecha_hasta)

    if estado:
        reclamos = reclamos.filter(estado_id=estado)

    if vecino:
        reclamos = reclamos.filter(id_contribuyente=vecino)

    if tipo:
        reclamos = reclamos.filter(tipo_reclamo_id=tipo)

    form = ReclamoForm()

    if request.method == 'POST':

        reclamo_id = request.POST.get('reclamo_id')

        estado_anterior = None
        tipo_anterior = None

        comentario_operador = request.POST.get('comentario_operador', '')
        if reclamo_id:
            # Editamos el reclamo
            reclamo = Reclamo.objects.get(id=reclamo_id)
            vecino_original = reclamo.id_contribuyente

            # Guardamos valores anteriores para ver si cambio algo y actualizar luego el log
            estado_anterior = reclamo.estado
            tipo_anterior = reclamo.tipo_reclamo
            prioridad_anterior = reclamo.prioridad
            titulo_anterior = reclamo.titulo
            descripcion_anterior = reclamo.descripcion
            vecino_anterior = reclamo.id_contribuyente

            form = ReclamoForm(request.POST, instance=reclamo)

        else:
            # Nuevo reclamo
            form = ReclamoForm(request.POST)

        if form.is_valid():

            reclamo = form.save(commit=False)
            reclamo.id_contribuyente = vecino_original

            if not reclamo_id:
                reclamo.usuario = user

            reclamo.usuario_ult_modificacion = user

            reclamo.save()

            if reclamo_id:

                cambios = False

                historial = HistorialReclamo(
                    reclamo=reclamo,
                    usuario=user,
                    accion="Actualizacion reclamo",
                    comentario=comentario_operador
                )

                if estado_anterior != reclamo.estado:
                    historial.estado_anterior = estado_anterior
                    historial.estado_nuevo = reclamo.estado
                    cambios = True

                if tipo_anterior != reclamo.tipo_reclamo:
                    historial.tipo_anterior = tipo_anterior
                    historial.tipo_nuevo = reclamo.tipo_reclamo
                    cambios = True

                if prioridad_anterior != reclamo.prioridad:
                    historial.prioridad_anterior = prioridad_anterior
                    historial.prioridad_nueva = reclamo.prioridad
                    cambios = True

                if titulo_anterior != reclamo.titulo:
                    historial.titulo_anterior = titulo_anterior
                    historial.titulo_nuevo = reclamo.titulo
                    cambios = True

                if descripcion_anterior != reclamo.descripcion:
                    historial.descripcion_anterior = descripcion_anterior
                    historial.descripcion_nueva = reclamo.descripcion
                    cambios = True

                if vecino_anterior != reclamo.id_contribuyente:
                    historial.vecino_anterior = vecino_anterior
                    historial.vecino_nuevo = reclamo.id_contribuyente
                    cambios = True

                if cambios or comentario_operador:
                    historial.save()
            else:

                HistorialReclamo.objects.create(
                    reclamo=reclamo,
                    usuario=user,
                    accion="Nuevo reclamo",
                    comentario=comentario_operador,
                    estado_nuevo=reclamo.estado,
                    tipo_nuevo=reclamo.tipo_reclamo,
                    prioridad_nueva=reclamo.prioridad,
                    titulo_nuevo=reclamo.titulo,
                    descripcion_nueva=reclamo.descripcion,
                    vecino_nuevo=reclamo.id_contribuyente
                )

            return redirect('inicio')
    estados = EstadoReclamo.objects.filter(activo=True)
    tipos = TipoReclamo.objects.filter(activo=True)

    return render(request, 'reclamos/inicio.html', {
        'reclamos': reclamos,
        'form': form,
        'estados': estados,
        'tipos': tipos
    })

@login_required
def lista_reclamos(request):

    reclamos = Reclamo.objects.all()
    form = ReclamoForm()

    if request.method == 'POST':
        form = ReclamoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_reclamos')

    estados = EstadoReclamo.objects.filter(activo=True)
    tipos = TipoReclamo.objects.filter(activo=True)

    return render(request, 'reclamos/lista.html', {
        'reclamos': reclamos,
        'form': form,
        'estados': estados,
        'tipos': tipos
    })

@login_required
def obtener_reclamo(request, id):

    reclamo = Reclamo.objects.get(id=id)

    data = {
        "id": reclamo.id,
        "id_contribuyente": reclamo.id_contribuyente,
        "titulo": reclamo.titulo,
        "descripcion": reclamo.descripcion,
        "prioridad": reclamo.prioridad,
        "estado": reclamo.estado.id,
        "tipo_reclamo": reclamo.tipo_reclamo.id
    }

    return JsonResponse(data)

@login_required
def obtener_historial(request, id):

    historial = HistorialReclamo.objects.filter(
        reclamo_id=id
    ).select_related(
        'usuario',
        'estado_anterior',
        'estado_nuevo',
        'tipo_anterior',
        'tipo_nuevo'
    ).order_by('-fecha')

    data = []

    for h in historial:

        cambios = []

        if h.estado_anterior != h.estado_nuevo:
            cambios.append(
                f"Estado: {h.estado_anterior or '-'} → {h.estado_nuevo or '-'}"
            )

        if h.tipo_anterior != h.tipo_nuevo:
            cambios.append(
                f"Tipo: {h.tipo_anterior or '-'} → {h.tipo_nuevo or '-'}"
            )

        if h.prioridad_anterior != h.prioridad_nueva:
            cambios.append(
                f"Prioridad: {h.prioridad_anterior or '-'} → {h.prioridad_nueva or '-'}"
            )

        if h.titulo_anterior != h.titulo_nuevo:
            cambios.append("Título modificado")

        if h.descripcion_anterior != h.descripcion_nueva:
            cambios.append("Descripción modificada")

        if h.vecino_anterior != h.vecino_nuevo:
            cambios.append(
                f"Vecino: {h.vecino_anterior or '-'} → {h.vecino_nuevo or '-'}"
            )

        data.append({
            "fecha": h.fecha.strftime("%d/%m/%Y %H:%M"),
            "usuario": h.usuario.username if h.usuario else "-",
            "accion": h.accion,
            "cambios": "<br>".join(cambios) if cambios else "-",
            "comentario": h.comentario or "-"
        })

    return JsonResponse(data, safe=False)
