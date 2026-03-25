from rest_framework.test import APITestCase
from rest_framework import status
from apps.users.models import User
from apps.users.serializers import ChangeUserStatusSerializer
from django.urls import reverse


class AuthTests(APITestCase):

    def _simple_register_payload(self, **overrides):
        payload = {
            "correo_electronico": "test@example.com",
            "contrasena": "password123",
            "confirmar_contrasena": "password123",
            "rol": "CLIENTE",
        }
        payload.update(overrides)
        return payload

    def _register_payload(self, **overrides):
        payload = self._simple_register_payload(
            nombre_completo="Test Usuario",
            tipo_documento="CC",
            numero_documento="123456789",
            fecha_nacimiento="1990-01-01",
            fecha_expedicion="2008-01-01",
            telefono="+573001112233",
            direccion="Calle 123 #45-67",
            nombre_negocio="Negocio Test",
            tipos_producto="Ropa y accesorios",
            rol="VENDEDOR",
        )
        payload.update(overrides)
        return payload

    def test_register_success(self):
        """Prueba registro exitoso"""
        data = self._simple_register_payload()
        url = reverse("register")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().status, User.Status.PENDING)

    def test_register_vendor_requires_full_data(self):
        data = self._simple_register_payload(rol="VENDEDOR")
        url = reverse("register")
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        """Prueba contraseñas que no coinciden"""
        data = self._register_payload(confirmar_contrasena="password456")
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

    def test_change_user_status_serializer_accepts_spanish_estado(self):
        serializer = ChangeUserStatusSerializer(data={"estado": "ACTIVO"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["status"], User.Status.ACTIVE)

    def test_change_user_status_serializer_accepts_denegado_alias(self):
        serializer = ChangeUserStatusSerializer(data={"estado": "DENEGADO"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["status"], User.Status.REJECTED)
