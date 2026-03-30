import calendar
import locale
from os import write


from django.contrib.auth.models import User
from django.db.models.functions import ExtractMonth
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin  #Esto restringe las vistas si el usuario no tiene sesion
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Reclamo, HistorialReclamo, ReclamoFoto, Contribuyente
from .forms import ReclamoForm
from django.http import JsonResponse
from .models import HistorialReclamo, EstadoReclamo
from datetime import datetime
from django.utils import timezone
from .models import EstadoReclamo, TipoReclamo
from django.db.models import Count
from django.utils.timezone import now
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from datetime import timedelta
from .utils_email import enviar_mail_reclamo_async_html



# Create your views here.
@login_required(login_url='/login/')
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
    ).annotate(
        total_fotos=Count('fotos')
    ).filter(
        fecha_creacion__date__gte=fecha_desde,
        fecha_creacion__date__lte=fecha_hasta
    )

    # FILTRO POR GRUPO (Siempre asignar un grupo, sino muestra todo al usuario)
    if request.user.groups.filter(name="ADMINISTRADOR").exists():
        pass
    else:
        grupos = list(request.user.groups.values_list('name', flat=True))

        if grupos:
            reclamos = reclamos.filter(tipo_reclamo__nombre__in=grupos
       )
        else:
            reclamos = reclamos.none()

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
        ).annotate(
        total_fotos=Count('fotos')
        ).filter(
            estado__nombre="EN_PROCESO",
            fecha_creacion__lt=timezone.now() - timedelta(days=5)
        )

    form = ReclamoForm()

    if request.method == 'POST':
        print ("Entra por request.method == 'POST'")
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

            es_nuevo = reclamo._state.adding

            if reclamo_id:
                reclamo.id_contribuyente = vecino_original

            if not reclamo_id:
                reclamo.usuario = user

            reclamo.usuario_ult_modificacion = user

            if reclamo.estado.nombre == "FINALIZADO" and not reclamo.fecha_cierre:
                reclamo.fecha_cierre = timezone.now()

            reclamo.save()
            #Enviamos mail al contribuyente por un nuevo reclamo

            if (es_nuevo and reclamo.id_contribuyente.email):
                print("Enviando mail")
                enviar_mail_reclamo_async_html(reclamo,f"Reclamo recibido Nº {reclamo.numero}","Su reclamo fue registrado correctamente.")

            #guardamos las fotos que se cargaron el en input
            fotos = request.FILES.getlist("fotos")
            cantidad_fotos = 0
            for f in fotos:
                ReclamoFoto.objects.create(
                    reclamo=reclamo,
                    imagen=f
                )
                cantidad_fotos = cantidad_fotos + 1

            if cantidad_fotos > 0:
                HistorialReclamo.objects.create(
                    reclamo=reclamo,
                    usuario=user,
                    accion="Carga de imagenes",
                    comentario=f"Se agregaron {cantidad_fotos} imagen/es"
                )

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
                    historial.vecino_nuevo = reclamo.id_contribuyente.id if reclamo.id_contribuyente else None
                    cambios = True

                if cambios or comentario_operador:
                    historial.save()

                    if estado_anterior != reclamo.estado and reclamo.estado.nombre == "FINALIZADO":
                        # Solo enviamos si cambiamos el estado a Finalizado, si es otra modificacion no se envia notificacion
                        enviar_mail_reclamo_async_html(
                            reclamo,
                            f"Reclamo Nº {reclamo.numero} finalizado",
                            "Su reclamo ha sido resuelto. ¡Gracias por comunicarse con nosotros!"
                        )

                    else:
                        #Solo enviamos si cambiamos el estado, si es otra modificacion no se envia notificacion
                        if estado_anterior != reclamo.estado:
                            enviar_mail_reclamo_async_html(
                                reclamo,
                                f"Actualización de reclamo Nº {reclamo.numero}",
                                f"El estado de su reclamo cambió a: {reclamo.estado}"
                            )
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
                    vecino_nuevo=reclamo.id_contribuyente.id if reclamo.id_contribuyente else None,
                )

            return redirect('dashboard')


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
    vecinos = Contribuyente.objects.all().order_by('apellido')
    es_sector = not request.user.groups.filter(name="ADMINISTRADOR").exists()
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    # Obtener fecha actual
    ahora = datetime.now()
    # Formato largo: Día, dia de mes de año
    fecha_larga = ahora.strftime("%A, %d de %B de %Y").capitalize()

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
        'data_estado': data_estado,
        'vecinos' : vecinos,
        'es_sector': es_sector,
        'fecha': fecha_larga
    })


@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def obtener_reclamo(request, id):
    try:
        reclamo = Reclamo.objects.select_related(
            'id_contribuyente', 'estado', 'tipo_reclamo'
        ).get(id=id)
    except Reclamo.DoesNotExist:
        return JsonResponse({"error": "Reclamo no encontrado"}, status=404)
    except Exception as e:
        # Captura cualquier otro error inesperado
        return JsonResponse({"error": str(e)}, status=500)

    data = {
        "id": reclamo.id,
        "id_contribuyente": reclamo.id_contribuyente.id if reclamo.id_contribuyente else None,
        "titulo": reclamo.titulo or "",
        "descripcion": reclamo.descripcion or "",
        "prioridad": reclamo.prioridad if reclamo.prioridad is not None else 0,
        "estado": reclamo.estado.id if reclamo.estado else None,
        "tipo_reclamo": reclamo.tipo_reclamo.id if reclamo.tipo_reclamo else None
    }

    return JsonResponse(data)



@login_required(login_url='/login/')
def eliminar_reclamo(request, id):
    try:
        reclamo = Reclamo.objects.get(id=id)

        estado_anulado = EstadoReclamo.objects.get(nombre="ANULADO")

        reclamo.estado = estado_anulado
        reclamo.save()

        return JsonResponse({
            "id": reclamo.id,
            "ret": 1
        })

    except Exception as e:

        return JsonResponse({
            "id": id,
            "ret": -1,
            "error": str(e)
        })

@login_required(login_url='/login/')
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

def fotos_reclamo(request, id):
    fotos = ReclamoFoto.objects.filter(reclamo_id=id)
    data = []
    for f in fotos:
        data.append({
            "id" : f.id,
            "url": f.imagen.url,
        })
    return JsonResponse(data, safe=False)

def eliminar_foto(request, id):
    try:
        foto = ReclamoFoto.objects.get(id=id)
        foto.imagen.delete()
        foto.delete()
        return JsonResponse({"ret": 1})
    except:
        return JsonResponse({"ret": -1})

def buscar_contribuyente(request):
    dni = request.GET.get("dni")
    if not dni:
        return JsonResponse({"existe": False})

    contribuyente = Contribuyente.objects.filter(dni=dni).first()
    if contribuyente:
        return JsonResponse({
            "existe": True,
            "apellido": contribuyente.apellido,
            "nombres": contribuyente.nombres,
            "telefono": contribuyente.telefono,
            "email": contribuyente.email
        })
    return JsonResponse({"existe": False})

def portal_reclamos(request):
    return render(request,"reclamos/portal.html")

def reclamo_wizard(request):

    if request.method == "POST":

        dni = request.POST.get("dni")
        apellido = request.POST.get("apellido")
        nombres = request.POST.get("nombres")
        telefono = request.POST.get("telefono")
        email = request.POST.get("email")

        tipo_id = request.POST.get("tipo")

        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        direccion = request.POST.get("direccion")

        contribuyente, creado = Contribuyente.objects.get_or_create(
            dni=dni,
            defaults={
                "apellido": apellido,
                "nombres": nombres,
                "telefono": telefono,
                "email": email
            }
        )

        estado = EstadoReclamo.objects.get(nombre="INGRESO")

        tipo = TipoReclamo.objects.get(id=tipo_id)

        usuario = User.objects.first()

        reclamo = Reclamo.objects.create(
            usuario=usuario,
            id_contribuyente=contribuyente,
            direccion=direccion,
            titulo=titulo,
            descripcion=descripcion,
            tipo_reclamo=tipo,
            estado=estado,
            prioridad=1
        )

        # Enviamos el mail al contribuyente
        if contribuyente.email:
            enviar_mail_reclamo_async_html(
                reclamo,
                f"Reclamo recibido Nº {reclamo.numero}",
                "Su reclamo fue registrado correctamente."
            )

        fotos = request.FILES.getlist("fotos")

        for foto in fotos:
            ReclamoFoto.objects.create(
                reclamo=reclamo,
                imagen=foto
            )

        return redirect("reclamo_confirmado", numero=reclamo.numero)

    tipos = TipoReclamo.objects.filter(activo=True).order_by("nombre")

    return render(
        request,
        "reclamos/reclamo_wizard.html",
        {"tipos": tipos}
    )

def reclamo_confirmado(request, numero):
    reclamo = Reclamo.objects.get(numero=numero)
    return render(
        request,
        "reclamos/reclamo_confirmado.html",
        {
            "reclamo": reclamo
        }
    )

def consultar_reclamo(request):
    numero = request.GET.get("numero")
    dni = request.GET.get("dni")

    reclamo = None
    historial = None
    error = None

    if numero and dni:
        numero = numero.strip().upper()

        reclamo_id = obtener_id_desde_numero(numero)

        if reclamo_id:
            try:
                reclamo = Reclamo.objects.select_related(
                    "estado",
                    "tipo_reclamo",
                    "id_contribuyente"
                ).get(
                    id=reclamo_id,
                    id_contribuyente__dni=dni
                )

                historial = reclamo.historial.all().order_by("fecha")

            except Reclamo.DoesNotExist:
                error = "No se encontró el reclamo con los datos ingresados"
        else:
            error = "Número de reclamo inválido"

    return render(request, "reclamos/portal.html", {
        "reclamo": reclamo,
        "historial": historial,
        "error": error
    })

def obtener_id_desde_numero(numero):
        try:
            return int(numero.split("-")[-1])
        except:
            return None
