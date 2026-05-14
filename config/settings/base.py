import environ
import dj_database_url
from pathlib import Path
from datetime import timedelta
import os

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Environment
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

# Security
SECRET_KEY = env("SECRET_KEY", default="django-insecure-fallback-key-for-build-purposes-only")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"] if DEBUG else [".railway.app", ".up.railway.app"],
)

# Encryption
ENCRYPTION_KEY = env("ENCRYPTION_KEY", default=None)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Permitir a Axios leer csrf token
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

if not DEBUG:
    SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Cookies Cross-Site (Vercel -> Railway)
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
else:
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

# Applications
INSTALLED_APPS = [
    "daphne", # Requerido para WebSockets (Debe ser el primero)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "cloudinary",
    "corsheaders",
    "channels",

    # Local Apps
    "apps.core",
    "apps.users",
    "apps.products",
    "apps.orders",
    "apps.geo",
    "apps.reviews",
    "apps.moderation",
    "apps.analytics",
    "apps.audit",
    "apps.chat",
    "apps.terms",

    # Third Party
    "drf_spectacular",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.BlockInactiveUserMiddleware",
    "apps.core.middleware.CurrentUserMiddleware",
]

AUTH_USER_MODEL = "users.User"

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

# --- REAL-TIME (CHANNELS) ---
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://localhost:6379/0")],
        },
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
if env("DATABASE_URL", default=None):
    DATABASES = {
        "default": env.db("DATABASE_URL")
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 600
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# CORS / CSRF
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https?://(www\.)?shopstarter\.online$",
    r"^https?://(www\.)?shopstarter\.vercel\.app$",
]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", 
    default=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "https://shopstarter.vercel.app", 
        "https://shopstarter.online",
        "http://shopstarter.online",
        "https://www.shopstarter.online",
        "http://www.shopstarter.online"
    ]
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS", 
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "https://shopstarter.vercel.app", 
        "https://shopstarter.online",
        "http://shopstarter.online",
        "https://www.shopstarter.online",
        "http://www.shopstarter.online"
    ]
)

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.core.authentication.CustomJWTAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("DRF_THROTTLE_ANON", default="10000/hour"),
        "user": env("DRF_THROTTLE_USER", default="20000/hour"),
        "login": env("DRF_THROTTLE_LOGIN", default="20/min"),
        "register": env("DRF_THROTTLE_REGISTER", default="50/hour"),
        "login_ip": "5/min",
        "login_user": "5/min",
        "ia_limit": "10/hour",
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SHOPSTARTER API',
    'DESCRIPTION': 'Documentación de la API del proyecto SHOPSTARTER',
    'VERSION': '1.0.0',
}

# --- CONFIGURACIÓN DE ARCHIVOS (MEDIA & STATIC) ---
# 1. Cloudinary (Media)
_cloudinary_url = env("CLOUDINARY_URL", default=None)
_cloud_name = env("CLOUDINARY_CLOUD_NAME", default=None)
_api_key = env("CLOUDINARY_API_KEY", default=None)
_api_secret = env("CLOUDINARY_API_SECRET", default=None)

if _cloudinary_url or (_cloud_name and _api_key and _api_secret):
    import cloudinary
    if _cloudinary_url and not all([_cloud_name, _api_key, _api_secret]):
        try:
            parts = _cloudinary_url.replace("cloudinary://", "").split("@")
            creds = parts[0].split(":")
            _api_key = creds[0]
            _api_secret = creds[1]
            _cloud_name = parts[1]
        except Exception:
            pass

    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": _cloud_name,
        "API_KEY": _api_key,
        "API_SECRET": _api_secret,
        "SECURE": True,
    }
    cloudinary.config(
        cloud_name=_cloud_name,
        api_key=_api_key,
        api_secret=_api_secret,
        secure=True
    )
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    MEDIA_URL = ""
    print("LOG: CLOUDINARY CONFIGURADO: Usando almacenamiento persistente en la nube.")
else:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    print("LOG: ADVERTENCIA: Cloudinary no detectado. Guardando fotos LOCALMENTE.")

MEDIA_ROOT = BASE_DIR / "media"

# 2. WhiteNoise (Static)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False  
WHITENOISE_USE_FINDERS = DEBUG       

if DEBUG:
    INSTALLED_APPS += ["django_extensions"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "debug.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

EMAIL_BACKEND = env("EMAIL_BACKEND", default="anymail.backends.brevo.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="ShopStarter <noreply@shopstarter.com>")
HUGGINGFACE_API_TOKEN = env("HUGGINGFACE_API_TOKEN", default="")
GROQ_API_KEY = env("GROQ_API_KEY", default="")

if not STATIC_ROOT.exists():
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

ANYMAIL = {
    "BREVO_API_KEY": env("BREVO_API_KEY", default=""),
}

FRONTEND_URL = env("FRONTEND_URL", default="https://shopstarter.online")
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8000")

SHOPSTARTER_TERMS_VERSION = env("SHOPSTARTER_TERMS_VERSION", default="1.0")
SHOPSTARTER_TERMS_CONTENT = {
    "v1": """ShopStarter - Términos y Condiciones de Privacidad

1. Uso de la plataforma: El usuario se compromete a utilizar ShopStarter únicamente para fines lícitos.
2. Responsabilidades: ShopStarter no se hace responsable por el contenido publicado por vendedores terceros.
3. Privacidad: Los datos personales son tratados conforme a la política de privacidad vigente.
4. Aceptación: Al registrarse o iniciar sesión, el usuario acepta estos términos en su versión actual.
""",
}

# CELERY Y REDIS
_redis_logger = logging.getLogger(__name__) if 'logging' in locals() else None

def _get_env_stripped(key: str) -> str:
    return os.environ.get(key, "").strip()

REDIS_URL = _get_env_stripped("REDIS_URL") or _get_env_stripped("REDIS_PRIVATE_URL")

if not REDIS_URL:
    R_HOST = _get_env_stripped("REDISHOST")
    R_PORT = _get_env_stripped("REDISPORT")
    R_USER = _get_env_stripped("REDISUSER")
    R_PASS = _get_env_stripped("REDISPASSWORD")
    if R_HOST and R_PORT:
        auth = f"{R_USER}:{R_PASS}@" if R_USER and R_PASS else ""
        REDIS_URL = f"redis://{auth}{R_HOST}:{R_PORT}"

if not REDIS_URL and not DEBUG:
    raise RuntimeError("REDIS_URL is not set.")

_REDIS_LOCALHOST_BROKER = "redis://localhost:6379/0"
_REDIS_LOCALHOST_BACKEND = "redis://localhost:6379/1"

CELERY_BROKER_URL = (
    _get_env_stripped("CELERY_BROKER_URL")
    or (f"{REDIS_URL}/0" if REDIS_URL else _REDIS_LOCALHOST_BROKER)
)
CELERY_RESULT_BACKEND = (
    _get_env_stripped("CELERY_RESULT_BACKEND")
    or (f"{REDIS_URL}/1" if REDIS_URL else _REDIS_LOCALHOST_BACKEND)
)

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_ALWAYS_EAGER", default=DEBUG and not REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100 # Previene memory leaks
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
