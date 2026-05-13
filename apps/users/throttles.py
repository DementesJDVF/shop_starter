from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'

class LoginIPRateThrottle(AnonRateThrottle):
    """
    ESCUDO ANTI-FUERZA BRUTA POR IP:
    Limita la cantidad de intentos de login que pueden venir de una misma dirección IP.
    Evita ataques distribuidos o escaneos masivos desde una sola fuente.
    """
    scope = 'login_ip'

class LoginUserRateThrottle(UserRateThrottle):
    """
    ESCUDO ANTI-FUERZA BRUTA POR CUENTA:
    Limita la cantidad de intentos de login para un mismo correo electrónico.
    Protege contra ataques de diccionario dirigidos a un usuario específico.
    """
    scope = 'login_user'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return None # El usuario ya está dentro, no aplica este throttle
            
        email = request.data.get('email')
        if not email:
            return None
            
        # Generar una llave única basada en el email
        return self.cache_format % {
            'scope': self.scope,
            'ident': email.strip().lower()
        }
