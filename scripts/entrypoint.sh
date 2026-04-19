#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

echo "--> Ejecutando migraciones..."
python manage.py migrate --noinput

echo "--> Recolectando archivos estáticos..."
# Este paso crea la carpeta /app/staticfiles/ y resuelve el UserWarning de WhiteNoise
python manage.py collectstatic --noinput

echo "--> Iniciando Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
