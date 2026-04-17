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
from django.utils import timezone
from .models import EstadoReclamo, TipoReclamo
from django.db.models import Count
from django.utils.timezone import now
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from datetime import timedelta
from .utils_email import enviar_mail_reclamo_async_html
from datetime import datetime, timedelta, date
from django.db.models import Count, ExpressionWrapper, F, DurationField, Avg
import calendar
from django.db.models import OuterRef, Subquery, Count
from django.conf import settings




# Create your views here.
from datetime import datetime, timedelta, date  # ðŸ”¥ agregado date
@login_required(login_url='/login/')
def inicio(request):

    import traceback

    user = request.user
    es_admin = request.user.groups.filter(name='ADMINISTRADOR').exists()
    es_sector = not es_admin
    hoy = timezone.now()

    # ------------------------
    # ESTADÍSTICAS
    # ------------------------
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

    tiempo_promedio = (
        f"{tiempos['promedio'].days} días"
        if tiempos['promedio']
        else "-"
    )

    # ------------------------
    # FECHAS
    # ------------------------
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if not fecha_desde or not fecha_hasta:
        primer_dia = hoy.replace(day=1)
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]

        fecha_desde = primer_dia.strftime('%Y-%m-%d')
        fecha_hasta = hoy.replace(day=ultimo_dia).strftime('%Y-%m-%d')

    # ------------------------
    # QUERY BASE
    # ------------------------
    reclamos = Reclamo.objects.select_related(
        'usuario', 'estado', 'tipo_reclamo'
    )

    # ------------------------
    # SEGURIDAD
    # ------------------------
    if not es_admin:
        grupos = list(request.user.groups.values_list('name', flat=True))

        if grupos:
            reclamos = reclamos.filter(
                tipo_reclamo__nombre__in=grupos
            ).distinct()
        else:
            reclamos = Reclamo.objects.none()

    # ------------------------
    # VER TODOS
    # ------------------------
    ver_todos = request.GET.get("ver_todos") in ["1", "true", "True", "on"]

    # ------------------------
    # FILTROS
    # ------------------------
    if not ver_todos:

        if request.GET.get('estado'):
            reclamos = reclamos.filter(estado_id=request.GET.get('estado'))

        if request.GET.get('vecino'):
            reclamos = reclamos.filter(id_contribuyente=request.GET.get('vecino'))

        if request.GET.get('tipo'):
            reclamos = reclamos.filter(tipo_reclamo_id=request.GET.get('tipo'))

        if request.GET.get('prioridad'):
            reclamos = reclamos.filter(prioridad=request.GET.get('prioridad'))

        if request.GET.get("demorados"):
            reclamos = reclamos.filter(
                estado__nombre="EN_PROCESO",
                fecha_creacion__lt=hoy - timedelta(days=5)
            )

        if fecha_desde:
            fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
            reclamos = reclamos.filter(fecha_creacion__gte=fecha_desde_dt)

        if fecha_hasta:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d")
            fecha_hasta_dt = fecha_hasta_dt.replace(hour=23, minute=59, second=59)
            reclamos = reclamos.filter(fecha_creacion__lte=fecha_hasta_dt)

    # ------------------------
    # ORDEN + LIMIT
    # ------------------------
    reclamos = reclamos.annotate(
        total_fotos=Count('fotos')
    ).order_by('-fecha_creacion')

    if ver_todos:
        reclamos = reclamos[:200]

    # ------------------------
    # FORM
    # ------------------------
    form = ReclamoForm(es_admin=es_admin)

    # ------------------------
    # POST (AJAX SEGURO)
    # ------------------------
    if request.method == 'POST':

        try:
            reclamo_id = request.POST.get('reclamo_id')

            if reclamo_id:
                try:
                    reclamo = Reclamo.objects.get(id=reclamo_id)
                    original = Reclamo.objects.get(id=reclamo_id)
                    vecino_original = reclamo.id_contribuyente
                except Reclamo.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "message": "Reclamo no encontrado"
                    }, status=404)
            else:
                reclamo = None
                original = None
                vecino_original = None

            form = ReclamoForm(
                request.POST,
                request.FILES,
                instance=reclamo if reclamo_id else None,
                es_admin=es_admin
            )

            if not form.is_valid():
                return JsonResponse({
                    "success": False,
                    "message": "Error de validación",
                    "errors": form.errors
                }, status=400)

            reclamo = form.save(commit=False)

            dni = request.POST.get("dni", "").strip()
            apellido = request.POST.get("apellido", "").strip().upper()
            nombres = request.POST.get("nombres", "").strip().upper()
            telefono = request.POST.get("telefono", "").strip().upper()
            email = request.POST.get("email", "").strip().lower()

            if dni:
                contribuyente, creado = Contribuyente.objects.get_or_create(
                    dni=dni,
                    defaults={
                        "apellido": apellido,
                        "nombres": nombres,
                        "telefono": telefono,
                        "email": email
                    }
                )

                if not creado:
                    # actualizar solo si vino dato nuevo
                    if apellido:
                        contribuyente.apellido = apellido
                    if nombres:
                        contribuyente.nombres = nombres
                    if telefono:
                        contribuyente.telefono = telefono
                    if email:
                        contribuyente.email = email

                    contribuyente.save()

                reclamo.id_contribuyente = contribuyente

            else:
                contribuyente = Contribuyente.objects.get(dni="999999999")
                reclamo.id_contribuyente = contribuyente

            reclamo.dni_ingresado = dni
            reclamo.apellido_contacto = apellido.upper() or contribuyente.apellido
            reclamo.nombres_contacto = nombres.upper() or contribuyente.nombres
            reclamo.telefono_contacto = telefono or contribuyente.telefono
            reclamo.email_contacto = email.lower() or contribuyente.email.lower()


            # restricciones
            if not es_admin and reclamo_id:
                reclamo.titulo = original.titulo
                reclamo.descripcion = original.descripcion
                reclamo.tipo_reclamo = original.tipo_reclamo

            if reclamo_id and not request.POST.get("dni"):
                reclamo.id_contribuyente = vecino_original
            else:
                reclamo.usuario = user

            reclamo.usuario_ult_modificacion = user

            # cierre automático
            if reclamo.estado_id:
                if reclamo.estado.nombre == "FINALIZADO" and not reclamo.fecha_cierre:
                    reclamo.fecha_cierre = timezone.now()

            reclamo.save()

            # ------------------------
            # FOTOS (sin duplicar)
            # ------------------------
            fotos = request.FILES.getlist("fotos")
            cantidad_fotos = len(fotos)

            for foto in fotos:
                ReclamoFoto.objects.create(
                    reclamo=reclamo,
                    imagen=foto
                )

            # ------------------------
            # HISTORIAL
            # ------------------------
            accion = "MODIFICACION" if reclamo_id else "CREACION"

            if cantidad_fotos > 0:
                accion = f"AGREGO_{cantidad_fotos}_FOTOS" if cantidad_fotos > 1 else "AGREGO_FOTO"

            comentario = request.POST.get("comentario_operador") or ""

            try:
                HistorialReclamo.objects.create(
                    reclamo=reclamo,
                    usuario=user,
                    accion=accion,
                    estado_anterior=original.estado if original and original.estado else None,
                    estado_nuevo=reclamo.estado if reclamo.estado else None,
                    prioridad_anterior=original.prioridad if original else None,
                    prioridad_nueva=reclamo.prioridad if reclamo else None,
                    titulo_anterior=original.titulo if original else None,
                    titulo_nuevo=reclamo.titulo,
                    descripcion_anterior=original.descripcion if original else None,
                    descripcion_nueva=reclamo.descripcion,
                    comentario=comentario
                )
            except Exception as e:
                print("ERROR HISTORIAL:", str(e))

            #Enviamos mail si se actualizo el estado
            # ------------------------
            try:
                if reclamo.id_contribuyente and reclamo.id_contribuyente.email:
                    PRIORIDAD_LABELS = {
                        1: "Baja",
                        2: "Media",
                        3: "Alta"
                    }
                    cambios_mail = []

                    if original:
                        if original.estado != reclamo.estado:
                            cambios_mail.append(f"Estado: {original.estado} → {reclamo.estado}")

                        if original.prioridad != reclamo.prioridad:
                            cambios_mail.append(f"Prioridad: {PRIORIDAD_LABELS.get(original.prioridad, '-')} → {PRIORIDAD_LABELS.get(reclamo.prioridad, '-')}")

                    if cambios_mail:
                        mensaje = "<br>".join([f"<strong>{c}</strong>" for c in cambios_mail])

                        enviar_mail_reclamo_async_html(
                            reclamo,
                            f"Actualización de reclamo Nº {reclamo.numero}",
                            f"Su reclamo tuvo cambios: {mensaje}"
                        )

            except Exception as e:
                print("ERROR MAIL:", str(e))

            return JsonResponse({
                "success": True,
                "message": "✔ Guardado correctamente",
                "reclamo_id": reclamo.id
            })

        except Exception as e:
            print(traceback.format_exc())

            return JsonResponse({
                "success": False,
                "message": str(e)
            }, status=500)

    # ------------------------
    # CONTEXTO
    # ------------------------
    estados = EstadoReclamo.objects.filter(activo=True)
    tipos = TipoReclamo.objects.filter(activo=True)
    vecinos = Contribuyente.objects.all().order_by('apellido')

    tipos_chart = Reclamo.objects.values(
        'tipo_reclamo__nombre'
    ).annotate(
        total=Count('id')
    ).order_by()

    labels_tipos = [t['tipo_reclamo__nombre'] for t in tipos_chart]
    data_tipos = [t['total'] for t in tipos_chart]

    reclamos_por_mes = Reclamo.objects.annotate(
        mes=ExtractMonth('fecha_creacion')
    ).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')

    labels_meses = [calendar.month_abbr[r['mes']] for r in reclamos_por_mes]
    data_meses = [r['total'] for r in reclamos_por_mes]

    estado_chart = Reclamo.objects.values(
        'estado__nombre'
    ).annotate(
        total=Count('id')
    )

    labels_estado = [e['estado__nombre'] for e in estado_chart]
    data_estado = [e['total'] for e in estado_chart]

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
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'vecinos': vecinos,
        'es_admin': es_admin,
        'es_sector': not es_admin,
        'labels_tipos': labels_tipos,
        'data_tipos': data_tipos,
        'labels_meses': labels_meses,
        'data_meses': data_meses,
        'labels_estado': labels_estado,
        'data_estado': data_estado,
        "session_age": settings.SESSION_COOKIE_AGE
    })

@login_required(login_url='/login/')
def lista_reclamos(request):

    reclamos = Reclamo.objects.all()
    es_admin = request.user.groups.filter(name='ADMINISTRADOR').exists()
    form = ReclamoForm(es_admin=es_admin)

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
        'fecha_fin_mes': fecha_fin_mes,
        "session_age": settings.SESSION_COOKIE_AGE,

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
	    "dni": reclamo.id_contribuyente.dni if reclamo.id_contribuyente else "",
    	"apellido": reclamo.id_contribuyente.apellido if reclamo.id_contribuyente else "",
   	    "nombres": reclamo.id_contribuyente.nombres if reclamo.id_contribuyente else "",
        "telefono": reclamo.id_contribuyente.telefono if reclamo.id_contribuyente else "",
        "email": reclamo.id_contribuyente.email if reclamo.id_contribuyente else "",
	    "direccion": reclamo.direccion or "",
        "entre_calle_1": reclamo.entre_calle_1,
        "entre_calle_2": reclamo.entre_calle_2,
        "apellido_contacto": reclamo.apellido_contacto,
        "nombres_contacto": reclamo.nombres_contacto,
        "telefono_contacto" : reclamo.telefono_contacto,
        "email_contacto" : reclamo.email_contacto,
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

    PRIORIDAD_LABELS = {
        1: "Baja",
        2: "Media",
        3: "Alta"
    }

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
                f"Estado: {h.estado_anterior or '-'} -> {h.estado_nuevo or '-'}"
            )

        if h.tipo_anterior != h.tipo_nuevo:
            cambios.append(
                f"Tipo: {h.tipo_anterior or '-'} -> {h.tipo_nuevo or '-'}"
            )

        if h.prioridad_anterior != h.prioridad_nueva:
            cambios.append(
                f"Prioridad: {PRIORIDAD_LABELS.get(h.prioridad_anterior, '-')} → {PRIORIDAD_LABELS.get(h.prioridad_nueva, '-')}"
            )

        if h.titulo_anterior != h.titulo_nuevo:
            cambios.append("Titulo modificado")

        if h.descripcion_anterior != h.descripcion_nueva:
            cambios.append("Descripcion modificada")

        if h.vecino_anterior != h.vecino_nuevo:
            cambios.append(
                f"Vecino: {h.vecino_anterior or '-'} -> {h.vecino_nuevo or '-'}"
            )
        if "AGREGO" in h.accion:
            if h.accion == "AGREGO_FOTO":
                cambios.append("Se agregó 1 foto")
            else:
                cantidad = h.accion.split("_")[1]
                cambios.append(f"Se agregaron {cantidad} fotos")

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

        dni = request.POST.get("dni", "").strip()
        apellido = request.POST.get("apellido", "").strip().upper()
        nombres = request.POST.get("nombres", "").strip().upper()
        telefono = request.POST.get("telefono", "").strip().upper()
        email = request.POST.get("email", "").strip().lower()

        tipo_id = request.POST.get("tipo")
        titulo = request.POST.get("titulo", "").strip().upper()
        descripcion = request.POST.get("descripcion", "").strip().upper()
        direccion = request.POST.get("direccion", "").strip().upper()
        entre_calle_1 = request.POST.get("entre_calle_1", "").strip().upper()
        entre_calle_2 = request.POST.get("entre_calle_2", "").strip().upper()

        # ---------------------------------
        # CONTRIBUYENTE
        # ---------------------------------
        if dni:
            contribuyente, creado = Contribuyente.objects.get_or_create(
                dni=dni,
                defaults={
                    "apellido": apellido,
                    "nombres": nombres,
                    "telefono": telefono,
                    "email": email
                }
            )

            if not creado:
                if apellido:
                    contribuyente.apellido = apellido
                if nombres:
                    contribuyente.nombres = nombres
                if telefono:
                    contribuyente.telefono = telefono
                if email:
                    contribuyente.email = email

                contribuyente.save()

        else:
            contribuyente = Contribuyente.objects.get(dni="999999999")

        # ---------------------------------
        # DATOS FIJOS
        # ---------------------------------
        estado = EstadoReclamo.objects.get(nombre="INGRESO")
        tipo = TipoReclamo.objects.get(id=tipo_id)
        usuario = User.objects.first()

        # ---------------------------------
        # CREAR RECLAMO
        # ---------------------------------
        reclamo = Reclamo.objects.create(
            usuario=usuario,
            id_contribuyente=contribuyente,
            direccion=direccion,
            entre_calle_1=entre_calle_1,
            entre_calle_2=entre_calle_2,
            titulo=titulo,
            descripcion=descripcion,
            tipo_reclamo=tipo,
            estado=estado,
            prioridad=1,

            dni_ingresado=dni,
            apellido_contacto=apellido or contribuyente.apellido,
            nombres_contacto=nombres or contribuyente.nombres,
            telefono_contacto=telefono or contribuyente.telefono,
            email_contacto=email or contribuyente.email
        )

        # ---------------------------------
        # MAIL
        # ---------------------------------
        destino = email or contribuyente.email

        if destino:
            enviar_mail_reclamo_async_html(
                reclamo,
                f"Reclamo recibido Nº {reclamo.numero}",
                "Su reclamo fue registrado correctamente."
            )

        # ---------------------------------
        # FOTOS
        # ---------------------------------
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
                error = "No se encontrÃ³ el reclamo con los datos ingresados"
        else:
            error = "NÃºmero de reclamo invÃ¡lido"

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
