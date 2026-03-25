from django.core.mail import send_mail
from django.conf import settings
import threading
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string



def enviar_mail_reclamo_html(reclamo, asunto, mensaje_principal):
    html_content = render_to_string("emails/reclamo_base.html", {
        "nombre": reclamo.id_contribuyente.nombres,
        "numero": reclamo.numero,
        "titulo": reclamo.titulo,
        "estado": reclamo.estado,
        "fecha": reclamo.fecha_creacion,
        "mensaje_principal": mensaje_principal,
        "url": f"www.reclamos.municipalidadvallemaria.com?numero={reclamo.numero}"
    })
    email = EmailMultiAlternatives(
        subject=asunto,
        body="Este correo requiere un cliente compatible con HTML",
        from_email=None,
        to=[reclamo.id_contribuyente.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()

def enviar_mail_reclamo_async_html(reclamo, asunto, mensaje):

    def task():
        enviar_mail_reclamo_html(reclamo, asunto, mensaje)

    threading.Thread(target=task).start()
