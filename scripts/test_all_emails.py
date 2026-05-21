import os
import sys
import django

# Añade el directorio del proyecto al PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_ROOT)

# Configura las variables de entorno para Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Inicializa Django
django.setup()

from apps.core.services.email_service import (
    send_welcome_email,
    send_password_reset_email,
    send_user_status_notification,
    send_order_confirmation_email,
    send_newsletter_email,
)
from apps.users.models import User

# Dirección de pruebas – cámbiala si lo deseas
TEST_EMAIL = "neythanayala670@gmail.com"

# Instancia de usuario dummy (no se guarda en BD)
user = User(username='testuser', email=TEST_EMAIL, full_name='Prueba Usuario')

print("--- Enviando correo de bienvenida ---")
print(send_welcome_email(user))

print("--- Enviando correo de restablecimiento de contraseña ---")
reset_url = "https://shopstarter.online/password-reset/demo-token"
print(send_password_reset_email(user, reset_url))

print("--- Enviando notificación de estado de usuario ---")
print(send_user_status_notification(user))

# Envío de confirmación de pedido (ejemplo genérico)
print("--- Enviando confirmación de pedido ---")
order_data = {"order_id": "ORD12345", "total": 99.99, "items": ["Producto A", "Producto B"]}
try:
    print(send_order_confirmation_email(user, order_data))
except Exception as e:
    print("Función de confirmación de pedido no disponible o error:", e)

# Envío de newsletter (ejemplo genérico)
print("--- Enviando newsletter ---")
newsletter_context = {"subject": "Newsletter Demo", "content": "Este es un ejemplo de newsletter."}
try:
    print(send_newsletter_email(user, newsletter_context))
except Exception as e:
    print("Función de newsletter no disponible o error:", e)
