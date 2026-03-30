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

#Base sqlite django
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

#Base postgreSql
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gmvm_db',
        'USER': 'gmvm_usr',
        'PASSWORD': '2701',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}