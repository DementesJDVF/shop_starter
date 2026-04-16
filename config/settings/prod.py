from .base import *
import dj_database_url

DEBUG = False

CORS_ALLOW_ALL_ORIGINS = False

# Aplicar opciones de producción solo si el motor es PostgreSQL
if DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql":
    DATABASES["default"].update({
        "CONN_MAX_AGE": 600,
        "OPTIONS": {"sslmode": "require"},
    })

# Seguridad
SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://*.onrender.com", 
        "https://shopstarter.online", 
        "https://*.shopstarter.online"
    ]
)

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", 
    default=["localhost", "127.0.0.1", ".up.railway.app", "shopstarter.online", ".shopstarter.online"]
)

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
