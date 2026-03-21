from .base import *
import dj_database_url

DEBUG = False

CORS_ALLOW_ALL_ORIGINS = False

DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )
}
