from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = []

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=0,
        ssl_require=False,
    )
}

# CORS (development only)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
