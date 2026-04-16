import os
import django
from django.conf import settings

# Simulamos que no hay DATABASE_URL (situación de build)
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

# Forzamos los ajustes de producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

try:
    django.setup()
    db_config = settings.DATABASES['default']
    print(f"Motor detectado: {db_config['ENGINE']}")
    print(f"Opciones (OPTIONS): {db_config.get('OPTIONS', {})}")
    
    # Verificamos si sslmode está presente indebidamente en SQLite
    if "sqlite3" in db_config['ENGINE'] and "sslmode" in db_config.get('OPTIONS', {}):
        print("ERROR: sslmode sigue presente en la configuración de SQLite.")
    else:
        print("ÉXITO: La configuración de base de datos es segura y compatible.")
        
except Exception as e:
    print(f"ERROR al cargar la configuración: {e}")
