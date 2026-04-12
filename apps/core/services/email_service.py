from django.core.mail import send_mail
from django.conf import settings

def send_product_status_notification(product):
    """
    Envía un correo electrónico al vendedor informando sobre el cambio de estado de su producto.
    """
    vendor_email = product.vendor.email
    status_label = "APROBADO" if product.status == "ACTIVE" else "RECHAZADO"
    
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
    Envía un correo al usuario informando si su cuenta fue APROBADA (ACTIVE) o RECHAZADA.
    """
    status_label = "ACTIVADA" if user.status == "ACTIVE" else "RECHAZADA/BLOQUEADA"
    
    subject = f"Actualización de tu cuenta en ShopStarter"
    message = f"""
    Hola {user.username},
    
    Te informamos que el estado de tu cuenta ha sido actualizado a: {status_label}.
    
    Si el estado es ACTIVADA, ya puedes iniciar sesión y empezar a vender o comprar.
    Si el estado es RECHAZADA, por favor contacta con soporte para más información.
    
    ¡Gracias por ser parte de ShopStarter!
    """
    
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
        print(f"Error enviando correo de usuario: {e}")
        return False
