from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Password123!',
            role='CLIENTE'
        )
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.me_url = reverse('me')
        self.refresh_url = reverse('token_refresh')

    def test_login_success_and_cookies_set(self):
        """Prueba que el login sea exitoso y establezca las cookies HttpOnly."""
        data = {
            'email': 'test@example.com',
            'password': 'Password123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertTrue(response.cookies['access_token']['httponly'])

    def test_access_with_valid_cookie(self):
        """Prueba que se pueda acceder a un endpoint protegido usando la cookie."""
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies['access_token'] = str(refresh.access_token)
        
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_logout_blacklists_token(self):
        """Prueba que el logout invalide el refresh token en la blacklist."""
        refresh = RefreshToken.for_user(self.user)
        refresh_token_str = str(refresh)
        
        self.client.cookies['refresh_token'] = refresh_token_str
        self.client.cookies['access_token'] = str(refresh.access_token)
        
        # Logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Intentar refrescar con el mismo token (debería fallar por estar en blacklist)
        self.client.cookies['refresh_token'] = refresh_token_str
        refresh_response = self.client.post(self.refresh_url)
        
        # SimpleJWT lanza 401 si el token está blacklisted
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_denied_without_token(self):
        """Prueba que un usuario no autenticado no pueda acceder."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_rejected(self):
        """Prueba que un token malformado sea rechazado."""
        self.client.cookies['access_token'] = "token-basura-total"
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
