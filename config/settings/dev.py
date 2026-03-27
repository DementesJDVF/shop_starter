from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = []

# CORS (development only)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
