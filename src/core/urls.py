from django.urls import path
from . import views
from .views import Login
from django.contrib.auth.views import LoginView, LogoutView


urlpatterns = [
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]