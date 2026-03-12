from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
# SISTEMA DASHBOARD ADMINISTRADOR
    path('', views.inicio, name='inicio'),
    path('lista/', views.lista_reclamos, name='lista_reclamos'),
    path('reclamo/<int:id>/', views.obtener_reclamo, name='obtener_reclamo'),
    path('reclamo/<int:id>/historial/', views.obtener_historial, name='obtener_historial'),
    path('reclamo/anular/<int:id>/', views.eliminar_reclamo, name='eliminar_reclamo'),
    path('fotos/<int:id>/', views.fotos_reclamo, name='fotos_reclamo'),
    path('foto/eliminar/<int:id>/', views.eliminar_foto),

    # PORTAL CIUDADANO
    path('portal/', views.portal_reclamos, name='portal_reclamos'),
    path('nuevo/', views.reclamo_wizard, name='reclamo_wizard'),
    path('consultar/', views.consultar_reclamo, name='consultar_reclamo'),
    path('buscar-contribuyente/', views.buscar_contribuyente, name='buscar_contribuyente'),
]