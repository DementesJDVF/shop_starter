from .base import *

DEBUG = True
ALLOWED_HOSTS = []

# Evita errores SMTP en desarrollo local.
# Los correos se imprimen en consola en lugar de intentar autenticarse con un servidor externo.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
