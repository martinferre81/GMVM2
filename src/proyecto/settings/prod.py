from .base import *

# Caducidad de sesión en segundos (30 minutos)
SESSION_COOKIE_AGE = 10 * 60  # 30 minutos = 1800 segundos

# Que la sesión se cierre al cerrar el navegador (opcional)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Usar sesión basada en cookies (por defecto es True)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


SECRET_KEY = 'django-insecure-4pq1c6%fp6bv+&@_kk@$mkk)h(n#k)iz4+a#z@twzmhkqr^e%z'

DEBUG = True

ALLOWED_HOSTS = [
    "reclamos.municipalidadvallemaria.com",
    "168.197.50.175",
    "localhost",
    "127.0.0.1"
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            '/home/gmvm/src/reclamos/templates',  # 👈 ESTO ES LO QUE FALTA
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'
STATIC_ROOT = '/home/gmvm/src/staticfiles'  # Carpeta donde Django recogerá los estáticos

# Opcional si tenés media (subidas de usuario)
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/gmvm/src/media'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gmvm_db_prod',
        'USER': 'gmvm_usr',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
