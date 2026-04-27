import threading
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User, UserSession

class AuthenticationConcurrencyTests(APITestCase):
    """
    PRUEBAS DE ESTRÉS Y CONCURRENCIA:
    Simula comportamientos de alta carga y ataques concurrentes para validar 
    la resiliencia del sistema de sesiones y throttling.
    """
    def setUp(self):
        self.user = User.objects.create_user(
            username='stress_user',
            email='stress@test.com',
            password='Password123!',
            role='CLIENTE'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_concurrent_logins_create_multiple_sessions(self):
        """Valida que múltiples logins simultáneos generen sesiones independientes sin colisiones."""
        def perform_login():
            from django.test import Client
            client = Client()
            client.post(self.login_url, {
                'email': 'stress@test.com',
                'password': 'Password123!'
            })

        threads = []
        for i in range(5):
            t = threading.Thread(target=perform_login)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verificar que se crearon 5 sesiones independientes
        self.assertEqual(UserSession.objects.filter(user=self.user, is_active=True).count(), 5)

    def test_brute_force_throttling_activation(self):
        """Valida que el sistema bloquee intentos tras superar el límite (5/min)."""
        data = {'email': 'stress@test.com', 'password': 'wrong-password'}
        
        # Realizar 5 intentos fallidos
        for i in range(5):
            self.client.post(self.login_url, data)
        
        # El 6to intento debe ser bloqueado por Throttling (HTTP 429)
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_concurrent_refresh_with_same_token_fails(self):
        """Valida que bajo concurrencia, el mismo refresh token solo pueda usarse UNA vez."""
        # 1. Login para obtener tokens
        res = self.client.post(self.login_url, {'email': 'stress@test.com', 'password': 'Password123!'})
        refresh_token = self.client.cookies['refresh_token'].value
        
        results = []
        def attempt_refresh():
            from django.test import Client
            c = Client()
            c.cookies['refresh_token'] = refresh_token
            # Importante: En SimpleJWT, el refresh es una petición POST
            response = c.post(reverse('token_refresh'))
            results.append(response.status_code)

        # 2. Disparar 5 peticiones simultáneas con el MISMO refresh token
        threads = []
        for _ in range(5):
            t = threading.Thread(target=attempt_refresh)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 3. Analizar resultados
        # Al menos uno debió ser 200 (si no hay colisión atómica perfecta)
        # Los demás DEBEN ser 401 (debido a la rotación y el blacklist inmediato)
        successes = results.count(status.HTTP_200_OK)
        failures = results.count(status.HTTP_401_UNAUTHORIZED)
        
        self.assertEqual(successes, 1, "Solo un refresh debe ser exitoso")
        self.assertGreaterEqual(failures, 4, "Los demás intentos deben ser rechazados")

    def test_session_invalidation_is_immediate(self):
        """Valida que la invalidación de una sesión afecte inmediatamente a los requests en curso."""
        # 1. Login
        res = self.client.post(self.login_url, {'email': 'stress@test.com', 'password': 'Password123!'})
        access_token = self.client.cookies['access_token'].value
        
        # 2. Verificar acceso
        self.client.cookies['access_token'] = access_token
        res_ok = self.client.get(reverse('me'))
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        
        # 3. Invalidar sesión manualmente (simulando logout o bloqueo)
        UserSession.objects.filter(user=self.user).update(is_active=False)
        
        # 4. Intentar acceso con el MISMO token
        res_fail = self.client.get(reverse('me'))
        self.assertEqual(res_fail.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(res_fail.data['code'], 'session_closed')
