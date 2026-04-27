import uuid
from django.conf import settings
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from apps.users.models import User
from apps.audit.application.services import AuditService

class AuthService:
    """
    ARQUITECTO DE SESIONES:
    Este servicio centraliza toda la lógica de autenticación, asegurando que se sigan
    las reglas de negocio y seguridad (Auditoría, Blacklisting, Invalidez de Access Tokens).
    """

    @staticmethod
    def login_user(user: User, ip_address: str, user_agent: str):
        """
        Inicia una sesión segura, crea un UserSession y genera tokens con 'jwt_key' y 'session_id'.
        """
        if not user.is_active or user.status == User.Status.BLOCKED:
            raise exceptions.PermissionDenied("Cuenta inactiva o bloqueada")

        # 1. Crear registro de sesión persistente
        from apps.users.models import UserSession
        session = UserSession.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 2. Generar tokens
        refresh = RefreshToken.for_user(user)
        
        # --- INYECCIÓN DE SEGURIDAD ---
        refresh['jwt_key'] = str(user.jwt_key)
        refresh['session_id'] = str(session.session_id)
        
        # Auditoría
        AuditService.log_login(user, ip_address=ip_address, user_agent=user_agent)
        
        return refresh

    @staticmethod
    def logout_user(refresh_token_str: str, user: User, ip_address: str, user_agent: str):
        """
        Cierra la sesión actual invalidando el Refresh Token y desactivando la UserSession.
        """
        try:
            if refresh_token_str:
                token = RefreshToken(refresh_token_str)
                session_id = token.get('session_id')
                
                # Desactivar sesión en DB
                from apps.users.models import UserSession
                UserSession.objects.filter(session_id=session_id).update(is_active=False)
                
                # Blacklist token
                token.blacklist()
        except (TokenError, InvalidToken):
            pass
            
        AuditService.log_logout(user, ip_address=ip_address, user_agent=user_agent)

    @staticmethod
    def logout_all_sessions(user: User, ip_address: str, user_agent: str):
        """
        ESTRATEGIA NUCLEAR: Cambia jwt_key y desactiva todas las sesiones en DB.
        """
        user.jwt_key = uuid.uuid4()
        user.save(update_fields=['jwt_key'])
        
        from apps.users.models import UserSession
        UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
        
        AuditService.log_logout(user, ip_address=ip_address, user_agent=user_agent)
    @staticmethod
    def log_failed_login(email: str, ip_address: str, user_agent: str, reason: str):
        """
        REGISTRO DE ATAQUES:
        Documenta intentos fallidos para detectar fuerza bruta. 
        Si el email no existe, se marca como sospechoso de escaneo.
        """
        AuditService._log(
            user=None,
            action_type="LOGIN_FAILED",
            instance=User(email=email),
            new_data={"reason": reason, "email_attempt": email},
            ip_address=ip_address,
            user_agent=user_agent,
            is_suspicious=True
        )

    @staticmethod
    def refresh_session(refresh_token_str: str, ip_address: str, user_agent: str):
        """
        REFRESCO BLINDADO (DB-First + Anti-Drift):
        Valida la sesión física en base de datos antes de emitir nuevos tokens.
        Garantiza que el session_id persista en la rotación de tokens.
        """
        try:
            # 1. Validación básica de firma y estructura
            refresh = RefreshToken(refresh_token_str)
            user_id = refresh.get('user_id')
            session_id = refresh.get('session_id')
            
            if not user_id or not session_id:
                raise exceptions.AuthenticationFailed("Token incompleto o malformado")

            # 2. Cargar usuario y validar estado
            user = User.objects.get(id=user_id)
            if not user.is_active or user.status == User.Status.BLOCKED:
                raise exceptions.AuthenticationFailed("Usuario inactivo o bloqueado")

            # 3. VALIDACIÓN ESTRICTA EN DB (Evita el re-uso tras logout)
            from apps.users.models import UserSession
            session = UserSession.objects.filter(
                session_id=session_id,
                user=user,
                is_active=True
            ).first()

            if not session:
                # Si la sesión no existe o fue desactivada, el refresh debe fallar SIEMPRE
                raise exceptions.AuthenticationFailed("La sesión ha expirado o ha sido cerrada")

            # 4. PROPAGACIÓN DE SEGURIDAD (Anti-Token Drift)
            # Aseguramos que el nuevo par de tokens mantenga la identidad de la sesión
            refresh['jwt_key'] = str(user.jwt_key)
            refresh['session_id'] = str(session.session_id)
            
            # Nota: SimpleJWT inyecta automáticamente los claims del refresh en el access token
            # generado durante la rotación, pero lo hacemos explícito para seguridad absoluta.
            refresh.access_token['session_id'] = str(session.session_id)
            refresh.access_token['jwt_key'] = str(user.jwt_key)
            
            # Actualizar última actividad de la sesión
            session.save(update_fields=['last_activity'])
            
            AuditService.log_refresh(user, ip_address=ip_address, user_agent=user_agent)
            return refresh
            
        except (TokenError, InvalidToken):
            raise exceptions.AuthenticationFailed("Token de refresco inválido o expirado")
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("El usuario ya no existe")
