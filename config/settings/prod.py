from .base import *
import dj_database_url

DEBUG = False

# Deshabilitar el Browsable API de DRF en producción (elimina 404s de /static/rest_framework/)
# En producción, solo necesitamos respuestas JSON puras
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

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

BASE_LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://*.up.railway.app",
        "https://shopstarter.online", 
        "http://shopstarter.online",
        "https://www.shopstarter.online",
        "http://www.shopstarter.online",
        "https://*.shopstarter.online",
        "https://shop-starter-production.up.railway.app",
        "https://shopstarter-production.up.railway.app"
    ]
) + BASE_LOCAL_ORIGINS

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", 
    default=[
        "https://shopstarter.vercel.app", 
        "https://shopstarter.online",
        "http://shopstarter.online",
        "https://www.shopstarter.online",
        "http://www.shopstarter.online",
        "https://shop-starter-production.up.railway.app",
        "https://shopstarter-production.up.railway.app"
    ]
) + BASE_LOCAL_ORIGINS

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", 
    default=["localhost", "127.0.0.1", ".up.railway.app", "shopstarter.online", ".shopstarter.online"]
)

# Estabilidad de Sesión
SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
