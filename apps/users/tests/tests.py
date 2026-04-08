from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from django.urls import reverse


class AuthTests(APITestCase):

    def test_register_success(self):
        """Prueba registro exitoso"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
        }
        url = reverse("register")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_password_mismatch(self):
        """Prueba contraseñas que no coinciden"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password456',
        }
        url = reverse("register")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Prueba login exitoso"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            role='CLIENTE'
        )
        data = {'email': 'test@example.com', 'password': 'password123'}
        url = reverse("login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_login_invalid_credentials(self):
        """Prueba credenciales inválidas"""
        data = {'email': 'wrong@email.com', 'password': 'wrongpass'}
        url = reverse("login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_login_trims_and_normalizes_email(self):
        """Permite login con email en mayúsculas o con espacios."""
        User.objects.create_user(
            username='trimuser',
            email='trim@example.com',
            password='password123',
            role='CLIENTE'
        )
        data = {'email': '  TRIM@EXAMPLE.COM  ', 'password': 'password123'}
        url = reverse("login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_password_keeps_spaces_as_real_chars(self):
        """No altera password: espacios forman parte de la contraseña."""
        User.objects.create_user(
            username='spacepass',
            email='spacepass@example.com',
            password='password123',
            role='CLIENTE'
        )
        data = {'email': 'spacepass@example.com', 'password': ' password123 '}
        url = reverse("login")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_register_user(self):
        return self.test_register_success()

    def test_login_returns_jwt(self):
        return self.test_login_success()

    def test_refresh_token_returns_new_access(self):
        User.objects.create_user(
            username='refreshuser',
            email='refresh@example.com',
            password='password123',
            role='CLIENTE'
        )
        login_url = reverse("login")
        login_response = self.client.post(login_url, {'email': 'refresh@example.com', 'password': 'password123'})
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_url = reverse("token_refresh")
        refresh_response = self.client.post(refresh_url, {'refresh': login_response.data['refresh_token']})
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_protected_endpoint_requires_auth(self):
        url = reverse("me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
