import json
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.db.models.fields.files import FieldFile

from apps.audit.infrastructure.models import AuditLog
from apps.core.middleware import get_current_ip, get_current_user


class AuditJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            if isinstance(o, FieldFile):
                return o.url if o else None
            # Soporte adicional para tipos que model_to_dict podría incluir
            if hasattr(o, '__str__'):
                return str(o)
            return super().default(o)
        except Exception:
            return str(o)


class AuditService:
    """
    EL GUARDIÁN DE LA INTEGRIDAD:
    Este servicio es el encargado de vigilar y registrar todo lo que sucede en el sistema.
    Desde quién cambió un precio, hasta quién intentó atacar el sistema con bots.
    """

    @staticmethod
    def _log(
        *,
        user,
        action_type,
        instance,
        previous_data=None,
        new_data=None,
        ip_address=None,
        user_agent=None,
        is_suspicious=False,
    ):
        """
        FUNCIÓN MAESTRA DE REGISTRO CON DEFENSA ACTIVA:
        Además de guardar el log, si la acción es sospechosa, dispara procesos 
        de seguridad y notificaciones al administrador.
        """
        if not user:
            user = get_current_user()
        
        if user and not user.is_authenticated:
            user = None
 
        if not ip_address:
            ip_address = get_current_ip()
        
        if not user_agent:
            from apps.core.middleware import get_current_user_agent
            user_agent = get_current_user_agent()

        # --- RESPUESTA ANTE AMENAZAS ---
        if is_suspicious:
            # 1. NOTIFICACIÓN INMEDIATA (Vía Brevo/Sistema de Alertas)
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                subject = f"🛑 ALERTA DE SEGURIDAD: {action_type}"
                message = (
                    f"¡Atención Administrador!\n\n"
                    f"Se ha detectado una actividad sospechosa en la plataforma:\n"
                    f"- Acción: {action_type}\n"
                    f"- IP de Origen: {ip_address}\n"
                    f"- Usuario: {user if user else 'Anónimo/Bot'}\n"
                    f"- Objeto: {instance}\n\n"
                    f"El sistema ha registrado los detalles para tu revisión en el Dashboard de Seguridad."
                )
                send_mail(
                    subject, message, 
                    settings.DEFAULT_FROM_EMAIL, 
                    [admin[1] for admin in settings.ADMINS] if hasattr(settings, 'ADMINS') and settings.ADMINS else ["admin@shopstarter.online"]
                )
            except Exception as e:
                # Si el correo falla, registramos el error pero no detenemos la protección
                print(f"Error enviando alerta de seguridad: {e}")

            # 2. EVALUACIÓN DE BLOQUEO (Límite de 3 intentos)
            if ip_address:
                suspicious_count = AuditLog.objects.filter(
                    ip_address=ip_address, 
                    is_suspicious=True
                ).count()
                
                if suspicious_count >= 2: # El tercer intento (este) dispara el bloqueo
                    from apps.core.models.security import BannedIP
                    BannedIP.objects.get_or_create(
                        ip_address=ip_address,
                        defaults={"reason": f"Bloqueo automático: Acumulación de {suspicious_count + 1} alertas de seguridad."}
                    )
            
            # 3. PENALIZACIÓN DE REPUTACIÓN (Si el usuario está logueado)
            if user and hasattr(user, 'reputation_score'):
                from decimal import Decimal
                user.reputation_score = max(Decimal('0.00'), user.reputation_score - Decimal('0.50'))
                user.save(update_fields=['reputation_score'])

        # --- IDENTIFICACIÓN DEL OBJETO ---
        content_type = None
        object_id = None
        object_repr = "N/A"
        
        if instance:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(instance.__class__)
            object_id = str(instance.pk)
            object_repr = str(instance)

        # Si no hay usuario ni instancia, no hay nada útil que loggear
        if not user and not instance and not new_data:
            return

        AuditLog.objects.create(
            user=user,
            action_type=action_type,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
            user_agent=user_agent,
            is_suspicious=is_suspicious,
        )


    @classmethod
    def log_create(cls, user, instance, ip_address=None):
        """Registra el nacimiento de un nuevo objeto (ej: un nuevo producto o usuario)."""
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.CREATE,
            instance=instance,
            new_data=cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_update(cls, user, instance, previous_data, ip_address=None):
        """
        REGISTRO DE CAMBIOS:
        Comparamos el estado anterior con el nuevo para guardar exactamente qué campo cambió.
        Es vital para saber "Quién cambio qué" en caso de errores o disputas.
        """
        new_data = cls._serialize(instance)
        diff = cls._compute_diff(previous_data, new_data)
        
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.UPDATE,
            instance=instance,
            previous_data=previous_data,
            new_data=new_data,
            ip_address=ip_address,
        )

    @staticmethod
    def _compute_diff(old, new):
        """
        LÓGICA DE DIFERENCIAS:
        Este 'Pequeño Genio' compara dos fotos del objeto y nos dice qué píxel cambió.
        Así ahorramos espacio en disco y el Admin ve solo lo que realmente se editó.
        """
        if not old: return new
        diff = {}
        for key in new:
            if old.get(key) != new.get(key):
                diff[key] = {
                    "from": old.get(key),
                    "to": new.get(key)
                }
        return diff

    @classmethod
    def log_delete(cls, user, instance, previous_data=None, ip_address=None):
        """Registra la eliminación definitiva de un dato. ¡Cuidado máximo aquí!"""
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.DELETE,
            instance=instance,
            previous_data=previous_data or cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_soft_delete(cls, user, instance, ip_address=None):
        """Registra cuando un objeto se marca como 'eliminado' (Soft Delete) pero sigue en la base de datos."""
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.SOFT_DELETE,
            instance=instance,
            previous_data=cls._serialize(instance),
            ip_address=ip_address,
        )

    @classmethod
    def log_restore(cls, user, instance, ip_address=None):
        """Registra cuando un objeto 'eliminado' vuelve a estar activo."""
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.RESTORE,
            instance=instance,
            new_data=cls._serialize(instance),
            ip_address=ip_address,
        )

    @staticmethod
    def _serialize(instance):
        """
        CONVERTIDOR A JSON:
        Traduce un objeto complejo de base de datos a un lenguaje que el Log pueda entender.
        """
        try:
            data = model_to_dict(instance)
            return json.loads(json.dumps(data, cls=AuditJSONEncoder))
        except Exception as e:
            # Red de seguridad: si algo falla, no bloqueamos al usuario, solo avisamos en el log.
            return {"error": "Serialization failed", "details": str(e), "repr": str(instance)}


    @classmethod
    def log_login(cls, user, ip_address=None, user_agent=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.LOGIN,
            instance=user,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @classmethod
    def log_logout(cls, user, ip_address=None, user_agent=None):
        cls._log(
            user=user,
            action_type=AuditLog.ActionType.LOGOUT,
            instance=user,
            ip_address=ip_address,
            user_agent=user_agent
        )

    @classmethod
    def log_refresh(cls, user, ip_address=None, user_agent=None):
        cls._log(
            user=user,
            action_type="REFRESH", # Usamos string si no está en choices o lo añadimos
            instance=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
