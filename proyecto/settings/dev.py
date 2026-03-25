from .base import *

SECRET_KEY = 'dev-key'

DEBUG = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "martinlisandro.of@gmail.com"
EMAIL_HOST_PASSWORD = "efqtnbnwieequbmg"
DEFAULT_FROM_EMAIL = "Municipalidad de Valle María <martinlisandro.of@gmail.com>"

ALLOWED_HOSTS = ["*"]

# 🔒 Trusted origins para CSRF con Cloudflare
CSRF_TRUSTED_ORIGINS = [
    'https://reclamos.municipalidadvallemaria.com'
]

# 📌 Redirección después del login
LOGIN_REDIRECT_URL = '/reclamos/'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
