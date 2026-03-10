import calendar

from django.db.models.functions import ExtractMonth
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
from django.db.models import Count
from django.utils.timezone import now
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from datetime import timedelta


# Create your views here.
@login_required
def inicio(request):
    user = request.user

    hoy = timezone.now()

    # Contar los reclamos del mes
    reclamos_mes = Reclamo.objects.filter(
        fecha_creacion__year=hoy.year,
        fecha_creacion__month=hoy.month
    ).count()

    reclamos_en_proceso = Reclamo.objects.filter(
        estado__nombre="EN_PROCESO"
    ).count()

    reclamos_finalizados = Reclamo.objects.filter(
        estado__nombre="FINALIZADO"
    ).count()

    reclamos_anulados = Reclamo.objects.filter(
        estado__nombre="ANULADO"
    ).count()

    limite_demora = hoy - timedelta(days=5)

    reclamos_demorados = Reclamo.objects.filter(
        estado__nombre="EN_PROCESO",
        fecha_creacion__lt=limite_demora
    ).count()

    tiempos = Reclamo.objects.filter(
        fecha_cierre__isnull=False
    ).annotate(
        duracion=ExpressionWrapper(
            F('fecha_cierre') - F('fecha_creacion'),
            output_field=DurationField()
        )
    ).aggregate(promedio=Avg('duracion'))

    tiempo_promedio = tiempos['promedio']

    if tiempo_promedio:
        dias = tiempo_promedio.days
        tiempo_promedio = f"{dias} días"
    else:
        tiempo_promedio = "-"

    # Fechas predeterminadas para el mes
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0)
    if hoy.month == 12:
        siguiente_mes = hoy.replace(year=hoy.year + 1, month=1, day=1)
    else:
        siguiente_mes = hoy.replace(month=hoy.month + 1, day=1)

    fecha_inicio_mes = primer_dia_mes.date()
    ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
    fecha_fin_mes = hoy.replace(day=ultimo_dia).date()

    # Obtener las fechas del formulario, si existen
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not fecha_desde:
        fecha_desde = fecha_inicio_mes.strftime('%Y-%m-%d')

    if not fecha_hasta:
        fecha_hasta = fecha_fin_mes.strftime('%Y-%m-%d')

    # QUERY BASE (todos los reclamos del mes)
    reclamos = Reclamo.objects.select_related(
        'usuario', 'estado', 'tipo_reclamo'
    ).filter(
        fecha_creacion__date__gte=fecha_desde,
        fecha_creacion__date__lte=fecha_hasta
    )

    # Filtros adicionales
    estado = request.GET.get('estado')
    vecino = request.GET.get('vecino')
    tipo = request.GET.get('tipo')
    prioridad = request.GET.get('prioridad')

    if estado:
        reclamos = reclamos.filter(estado_id=estado)

    if vecino:
        reclamos = reclamos.filter(id_contribuyente=vecino)

    if tipo:
        reclamos = reclamos.filter(tipo_reclamo_id=tipo)

    if prioridad:
        reclamos = reclamos.filter(prioridad=prioridad)

    if request.GET.get("demorados"):
        reclamos = Reclamo.objects.select_related(
            'usuario', 'estado', 'tipo_reclamo'
        ).filter(
            estado__nombre="EN_PROCESO",
            fecha_creacion__lt=timezone.now() - timedelta(days=5)
        )

    form = ReclamoForm()


    if request.method == 'POST':
        reclamo_id = request.POST.get('reclamo_id')

        estado_anterior = None
        tipo_anterior = None
        comentario_operador = request.POST.get('comentario_operador', '')

        if reclamo_id:
            # Editar un reclamo existente
            reclamo = Reclamo.objects.get(id=reclamo_id)
            vecino_original = reclamo.id_contribuyente

            # Guardar valores anteriores para ver si cambió algo y actualizar el historial
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
            if reclamo_id:
                reclamo.id_contribuyente = vecino_original

            if not reclamo_id:
                reclamo.usuario = user

            reclamo.usuario_ult_modificacion = user

            if reclamo.estado.nombre == "FINALIZADO" and not reclamo.fecha_cierre:
                reclamo.fecha_cierre = timezone.now()

            reclamo.save()

            if reclamo_id:
                cambios = False
                historial = HistorialReclamo(
                    reclamo=reclamo,
                    usuario=user,
                    accion="Actualización de reclamo",
                    comentario=comentario_operador
                )

                # Ver si ha habido cambios en los valores del reclamo
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
                    vecino_nuevo=reclamo.id_contribuyente,
                )

            return redirect('inicio')

    # Filtra los estados y tipos activos
    estados = EstadoReclamo.objects.filter(activo=True)
    tipos = TipoReclamo.objects.filter(activo=True)

    # Grafico reclamos por tipo
    datos_tipos = Reclamo.objects.values(
        'tipo_reclamo__nombre'
    ).annotate(
        total=Count('id')
    ).order_by('-total')

    labels_tipos = [d['tipo_reclamo__nombre'] for d in datos_tipos]
    data_tipos = [d['total'] for d in datos_tipos]

    #Datos para el grafico de reclamos por mes
    reclamos_mes_data = (
        Reclamo.objects
        .filter(fecha_creacion__year=hoy.year)
        .annotate(mes=ExtractMonth('fecha_creacion'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    labels_meses = []
    data_meses = []

    meses = [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
    ]

    for r in reclamos_mes_data:
        labels_meses.append(meses[r['mes'] - 1])
        data_meses.append(r['total'])

    #Datos para el grafico de reclamos por estados

    reclamos_estado = (
        Reclamo.objects
        .values('estado__nombre')
        .annotate(total=Count('id'))
    )

    labels_estado = [r['estado__nombre'] for r in reclamos_estado]
    data_estado = [r['total'] for r in reclamos_estado]

    return render(request, 'reclamos/inicio.html', {
        'reclamos': reclamos,
        'form': form,
        'estados': estados,
        'tipos': tipos,
        'reclamos_mes': reclamos_mes,
        'reclamos_en_proceso': reclamos_en_proceso,
        'reclamos_finalizados': reclamos_finalizados,
        'reclamos_anulados': reclamos_anulados,
        'tiempo_promedio': tiempo_promedio,
        'reclamos_demorados': reclamos_demorados,
        'fecha_inicio_mes': fecha_inicio_mes,
        'fecha_fin_mes': fecha_fin_mes,
        'fecha_desde': fecha_desde,  # fecha seleccionada
        'fecha_hasta': fecha_hasta,  # fecha seleccionada
        'labels_tipos': labels_tipos,
        'data_tipos': data_tipos,
        'labels_meses': labels_meses,
        'data_meses': data_meses,
        'labels_estado': labels_estado,
        'data_estado': data_estado
    })


@login_required
def lista_reclamos(request):

    reclamos = Reclamo.objects.all()
    form = ReclamoForm()

    hoy = timezone.now()
    primer_dia_mes = hoy.replace(day=1, hour=0, minute=0, second=0)

    # Fechas para setear los calendarios
    if hoy.month == 12:
        siguiente_mes = hoy.replace(year=hoy.year + 1, month=1, day=1)
    else:
        siguiente_mes = hoy.replace(month=hoy.month + 1, day=1)

    fecha_inicio_mes = primer_dia_mes.date()
    fecha_fin_mes = (siguiente_mes - timezone.timedelta(days=1)).date()

    if request.method == 'POST':
        form = ReclamoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_reclamos')

    reclamos_mes = reclamos.count()

    reclamos_en_proceso = reclamos.filter(
        estado__nombre="EN_PROCESO"
    ).count()

    reclamos_finalizados = reclamos.filter(
        estado__nombre="FINALIZADO"
    ).count()

    reclamos_anulados = reclamos.filter(
        estado__nombre="ANULADO"
    ).count()

    estados = EstadoReclamo.objects.filter(activo=True)
    tipos = TipoReclamo.objects.filter(activo=True)

    return render(request, 'reclamos/lista.html', {
        'reclamos': reclamos,
        'form': form,
        'estados': estados,
        'tipos': tipos,
        'reclamos_mes': reclamos_mes,
        'reclamos_en_proceso': reclamos_en_proceso,
        'reclamos_finalizados': reclamos_finalizados,
        'reclamos_anulados': reclamos_anulados,
        'fecha_inicio_mes': fecha_inicio_mes,
        'fecha_fin_mes': fecha_fin_mes

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
