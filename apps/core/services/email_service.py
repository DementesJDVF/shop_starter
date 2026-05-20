from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_product_status_notification(product):
    """
    Envía un correo electrónico al vendedor informando sobre el cambio de estado de su producto.
    """
    vendor_email = product.vendor.email
    status_label = "APROBADO" if product.status == "AVAILABLE" else "RECHAZADO"
    
    subject = f"Actualización de tu producto: {product.name}"
    
    reason_msg = f"\n\nMotivo del rechazo: {product.rejection_reason}" if product.status == "REJECTED" and product.rejection_reason else ""
    
    message = f"""
    Hola {product.vendor.username},
    
    Te informamos que tu producto '{product.name}' ha sido {status_label} por nuestro equipo de administración.
    
    Estado actual: {product.status}{reason_msg}
    
    ¡Gracias por usar ShopStarter!
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def send_user_status_notification(user):
    """
    Envía un correo profesional al usuario informando sobre el estado de su cuenta.
    """
    is_active = user.status == "ACTIVE"
    status_label = "CUENTA ACTIVADA" if is_active else "CUENTA RESTRINGIDA"
    bg_color = "#10b981" if is_active else "#ef4444"
    
    custom_message = (
        "¡Buenas noticias! Tu cuenta ha sido verificada. Ya puedes iniciar sesión, "
        "gestionar tus productos y realizar compras en nuestra plataforma."
        if is_active else 
        "Tu cuenta ha sido bloqueada o está bajo revisión por incumplir nuestras políticas de seguridad."
    )

    context = {
        'username': user.username,
        'status_label': status_label,
        'bg_color': bg_color,
        'custom_message': custom_message
    }
    
    html_content = render_to_string('emails/user_status.html', context)
    text_content = strip_tags(html_content)

    try:
        send_mail(
            f"Actualización de Seguridad: {status_label}",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando correo de usuario: {e}")
        return False

def send_password_reset_email(user, reset_url):
    """
    Envía un correo premium para restablecer la contraseña.
    """
    context = {
        'username': user.username,
        'reset_url': reset_url
    }
    
    html_content = render_to_string('emails/password_reset.html', context)
    text_content = strip_tags(html_content)
    
    try:
        send_mail(
            "Restablecer tu contraseña en ShopStarter",
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando correo de recuperación: {e}")
        return False

def send_welcome_email(user):
    """
    Envía un correo de bienvenida al cliente después de crear su cuenta.
    Ahora incluye un mensaje más amigable y personalizado con el nombre del usuario.
    """
    subject = f"¡Bienvenido a ShopStarter, {user.full_name or user.username}!"
    # Texto plano con saludo personalizado
    message = (
        f"Hola {user.full_name or user.username},\n\n"
        "¡Gracias por registrarte en ShopStarter! Estamos muy contentos de que te unas a nuestra comunidad.\n"
        "Explora el catálogo, compra y disfruta de la mejor experiencia.\n\n"
        "¡Éxitos!\n"
        "ShopStarter"
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error enviando correo de bienvenida: {e}")
        return False
