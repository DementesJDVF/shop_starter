import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.users.models import User
from apps.users.constants import UserRoles

email = "admin_extra@shopstarter.com"
username = "admin_extra"
password = "AdminPassword123!"

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        role=UserRoles.ADMIN
    )
    print(f"✅ Superusuario '{email}' creado exitosamente.")
    print(f"🔑 Password: {password}")
else:
    print(f"⚠️ El usuario '{email}' ya existe.")
