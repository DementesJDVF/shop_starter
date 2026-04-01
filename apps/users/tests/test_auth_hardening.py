from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [
            "rest_framework.throttling.AnonRateThrottle",
            "rest_framework.throttling.UserRateThrottle",
        ],
        "DEFAULT_THROTTLE_RATES": {
            "anon": "100/hour",
            "user": "100/hour",
            "login": "2/min",
            "register": "2/min",
        },
    }
)
class AuthHardeningTests(APITestCase):
    def _simple_register_payload(self, **overrides):
        payload = {
            "correo_electronico": "cliente@example.com",
            "contrasena": "password123",
            "confirmar_contrasena": "password123",
            "rol": "CLIENTE",
        }
        payload.update(overrides)
        return payload

    def _register_payload(self, **overrides):
        payload = self._simple_register_payload(
            nombre_completo="Vendedor Prueba",
            correo_electronico="vendedor@example.com",
            tipo_documento="CC",
            numero_documento="999888777",
            fecha_nacimiento="1991-02-03",
            fecha_expedicion="2009-02-03",
            telefono="+573102223344",
            direccion="Cra 10 #20-30",
            nombre_negocio="Tienda Demo",
            tipos_producto="Tecnología",
        )
        payload.update(overrides)
        return payload
    def test_register_allows_simple_customer_role(self):
        url = reverse("register")
        payload = self._simple_register_payload()

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="cliente@example.com").role, "CLIENTE")

    def test_register_allows_customer_or_vendor_role(self):
        url = reverse("register")
        payload = self._register_payload(rol="VENDEDOR")

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="vendedor@example.com").role, "VENDEDOR")

    def test_register_rejects_admin_self_assignment(self):
        url = reverse("register")
        payload = {
            "username": "adminwannabe",
            "email": "adminwannabe@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "role": "ADMIN",
        }
        payload = self._register_payload(
            correo_electronico="adminwannabe@example.com",
            numero_documento="111222333",
            rol="ADMIN",
        )

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_throttling_blocks_bruteforce_attempts(self):
        User.objects.create_user(
            username="normal",
            email="normal@example.com",
            password="password123",
            role="CLIENTE",
        )
        url = reverse("login")

        for _ in range(2):
            response = self.client.post(
                url,
                {"email": "normal@example.com", "password": "wrongpass"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        throttled = self.client.post(
            url,
            {"email": "normal@example.com", "password": "wrongpass"},)