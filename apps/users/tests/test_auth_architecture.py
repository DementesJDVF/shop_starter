from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class AuthenticationArchitectureTests(APITestCase):
    """
    SUITE DE PRUEBAS ARQUITECTÓNICAS Y DE SEGURIDAD:
    Valida que los nuevos mecanismos de blindaje (jwt_key, auditoría, multi-sesión)
    funcionen correctamente.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='arch_test',
            email='arch@test.com',
            password='Password123!',
            role='CLIENTE'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.me_url = reverse('me')
        self.refresh_url = reverse('token_refresh')

    def test_jwt_key_invalidation_works(self):
        """Prueba que cambiar el jwt_key invalide el access token inmediatamente."""
        # 1. Obtener un token válido
        refresh = RefreshToken.for_user(self.user)
        refresh['jwt_key'] = str(self.user.jwt_key)
        access_token = str(refresh.access_token)
        
        self.client.cookies['access_token'] = access_token
        
        # Verificar que funciona
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # 2. Simular Logout Global (Cambiar jwt_key)
        import uuid
        self.user.jwt_key = uuid.uuid4()
        self.user.save()
        
        # 3. Intentar usar el MISMO access token (Aún no expira cronológicamente)
        res_blocked = self.client.get(self.me_url)
        
        # Debe ser rechazado porque la jwt_key en el token no coincide con la DB
        self.assertEqual(res_blocked.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_blocked.data['code'], 'session_invalidated')

    def test_logout_all_devices_endpoint(self):
        """Prueba que el parámetro all_devices invalide todas las sesiones."""
        # 1. Login normal
        self.client.cookies['access_token'] = "dummy" # Simular cookie
        self.client.force_authenticate(user=self.user)
        
        old_jwt_key = self.user.jwt_key
        
        # 2. Llamar a logout con all_devices=True
        response = self.client.post(self.logout_url, {"all_devices": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Verificar que la jwt_key en la DB cambió
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.jwt_key, old_jwt_key)

    def test_audit_logs_created_on_login(self):
        """Verifica que se generen logs de auditoría en eventos críticos."""
        from apps.audit.infrastructure.models import AuditLog
        
        initial_count = AuditLog.objects.count()
        
        data = {'email': 'arch@test.com', 'password': 'Password123!'}
        self.client.post(self.login_url, data)
        
        # Debe haber al menos un log de LOGIN
        self.assertTrue(AuditLog.objects.filter(action_type='LOGIN', user=self.user).exists())
        self.assertGreater(AuditLog.objects.count(), initial_count)

    def test_refresh_token_validates_db_session(self):
        """Valida que el refresco consulte la UserSession en DB."""
        from apps.users.models import UserSession
        
        # 1. Login para generar sesión
        res = self.client.post(self.login_url, {'email': 'arch@test.com', 'password': 'Password123!'})
        refresh_token = self.client.cookies['refresh_token'].value
        
        # 2. Refrescar (Debe funcionar)
        self.client.cookies['refresh_token'] = refresh_token
        res_refresh = self.client.post(self.refresh_url)
        self.assertEqual(res_refresh.status_code, status.HTTP_200_OK)
        
        # 3. Desactivar sesión en DB manualmente
        UserSession.objects.filter(user=self.user).update(is_active=False)
        
        # 4. Intentar refrescar de nuevo con el MISMO refresh token
        res_fail = self.client.post(self.refresh_url)
        self.assertEqual(res_fail.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_fail.data['detail'], "La sesión ha expirado o ha sido cerrada")

    def test_refresh_propagates_session_id_to_both_tokens(self):
        """Valida que no haya 'Token Drift': session_id debe estar en access y refresh."""
        # 1. Login
        self.client.post(self.login_url, {'email': 'arch@test.com', 'password': 'Password123!'})
        refresh_token_str = self.client.cookies['refresh_token'].value
        
        # 2. Refrescar
        self.client.cookies['refresh_token'] = refresh_token_str
        res = self.client.post(self.refresh_url)
        
        # 3. Validar tokens en la respuesta (Cookies)
        new_access = self.client.cookies['access_token'].value
        new_refresh = self.client.cookies['refresh_token'].value
        
        # Decodificar tokens para ver los claims
        from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
        acc_decoded = AccessToken(new_access)
        ref_decoded = RefreshToken(new_refresh)
        
        # Deben tener el MISMO session_id y no ser nulos
        self.assertIsNotNone(acc_decoded.get('session_id'))
        self.assertEqual(acc_decoded.get('session_id'), ref_decoded.get('session_id'))
        self.assertEqual(acc_decoded.get('jwt_key'), str(self.user.jwt_key))
