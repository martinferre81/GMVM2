from .base import *

SECRET_KEY = 'django-insecure-4pq1c6%fp6bv+&@_kk@$mkk)h(n#k)iz4+a#z@twzmhkqr^e%z'

DEBUG = False

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "reclamos.municipalidadvallemaria.com",
    "www.reclamos.municipalidadvallemaria.com",
]

CSRF_TRUSTED_ORIGINS = [
    "http://reclamos.municipalidadvallemaria.com",
    "https://reclamos.municipalidadvallemaria.com",
    "http://www.reclamos.municipalidadvallemaria.com",
    "https://www.reclamos.municipalidadvallemaria.com",
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gmvm',
        'USER': 'gmvm_usr',
        'PASSWORD': 'gmvm_2701',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}