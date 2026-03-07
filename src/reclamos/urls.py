from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('', views.lista_reclamos, name='lista_reclamos'),
    path('reclamo/<int:id>/', views.obtener_reclamo, name='obtener_reclamo'),
    path('reclamo/<int:id>/historial/', views.obtener_historial, name='obtener_historial'),
]