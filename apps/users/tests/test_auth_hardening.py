from django.test import override_settings
from django.urls import reverse
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
            "rest_framework.throttling.ScopedRateThrottle",
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
    def test_register_allows_customer_or_vendor_role(self):
        url = reverse("register")
        payload = {
            "username": "vendedor",
            "email": "vendedor@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "role": "VENDEDOR",
            "is_human": True,
            "full_name": "Vendedor Test",
            "phone_number": "1234567890",
            "document_type": "CC",
            "document_number": "12345678",
            "birth_date": "1990-01-01"
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email="vendedor@example.com").role, "VENDEDOR")

    def test_register_rejects_admin_self_assignment(self):
        url = reverse("register")
        payload = {
            "username": "adminwannabe",
            "email": "adminwannabe@example.com",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "role": "ADMIN",
            "is_human": True
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_throttling_blocks_bruteforce_attempts(self):
        User.objects.create_user(
            username="normal",
            email="normal@example.com",
            password="Password123!",
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
            {"email": "normal@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
