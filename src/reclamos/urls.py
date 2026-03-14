from django.urls import path
from . import views

urlpatterns = [

# SISTEMA DASHBOARD
    path('', views.inicio, name='inicio'),
    path('lista/', views.lista_reclamos, name='lista_reclamos'),

    path('<int:id>/', views.obtener_reclamo, name='obtener_reclamo'),
    path('<int:id>/historial/', views.obtener_historial, name='obtener_historial'),
    path('anular/<int:id>/', views.eliminar_reclamo, name='eliminar_reclamo'),

    path('fotos/<int:id>/', views.fotos_reclamo, name='fotos_reclamo'),
    path('foto/eliminar/<int:id>/', views.eliminar_foto),

# PORTAL CIUDADANO
    path('portal/', views.portal_reclamos, name='portal_reclamos'),
    path('nuevo/', views.reclamo_wizard, name='reclamo_wizard'),
    path('consultar/', views.consultar_reclamo, name='consultar_reclamo'),
    path('buscar-contribuyente/', views.buscar_contribuyente, name='buscar_contribuyente'),
    path('confirmado/<str:numero>/', views.reclamo_confirmado, name='reclamo_confirmado'),
]