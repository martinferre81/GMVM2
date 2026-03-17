from .base import *

SECRET_KEY = 'django-insecure-4pq1c6%fp6bv+&@_kk@$mkk)h(n#k)iz4+a#z@twzmhkqr^e%z'

DEBUG = False

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "reclamos.municipalidadvallemaria.com",
    "www.reclamos.municipalidadvallemaria.com",
]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "martinlisandro.of@gmail.com"
EMAIL_HOST_PASSWORD = "efqtnbnwieequbmg"
DEFAULT_FROM_EMAIL = "Municipalidad de Valle María <martinlisandro.of@gmail.com>"

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
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}