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
            'role': 'CLIENTE'
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