from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from reclamos import views
from django.views.generic import TemplateView
from django.shortcuts import redirect

def index_redirect(request):
    return redirect('/dashboard/portal/')

def portal_redirect(request):
    return redirect('/')

urlpatterns = [
    path('', views.portal_reclamos, name='portal_root'),
    path('index.html', views.portal_reclamos),   
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('dashboard/', include('reclamos.urls')),
    path('dashboard/portal/', portal_redirect),
    path('admin/', admin.site.urls),
]
