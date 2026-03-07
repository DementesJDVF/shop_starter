from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


class PermissionTests(APITestCase):

    def create_user_with_role(self, role, is_active=True):
        user = User.objects.create_user(
            username=f"{role}_user",
            email=f"{role}@test.com",
            password="Test1234!"
        )
        user.role = role
        user.is_active = is_active
        user.save()
        return user

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    # ------------------------------
    # ADMIN ACCESS TESTS
    # ------------------------------

    def test_admin_can_access_admin_endpoint(self):
        admin = self.create_user_with_role("ADMIN")
        token = self.get_token(admin)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_cannot_access_admin_endpoint(self):
        client_user = self.create_user_with_role("CLIENTE")
        token = self.get_token(client_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_endpoint_requires_authentication(self):
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_access(self):
        inactive_user = self.create_user_with_role("ADMIN", is_active=False)
        token = self.get_token(inactive_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blocked_status_user_cannot_access(self):
        blocked_user = self.create_user_with_role("ADMIN", is_active=True)
        blocked_user.status = "BLOCKED"
        blocked_user.save(update_fields=["status"])
        token = self.get_token(blocked_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vendor_cannot_access_admin_features(self):
        vendor_user = self.create_user_with_role("VENDEDOR")
        token = self.get_token(vendor_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("admin_test")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_admin_cannot_change_role(self):
        client_user = self.create_user_with_role("CLIENTE")
        target_user = self.create_user_with_role("VENDEDOR")
        token = self.get_token(client_user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        url = reverse("change_user_role", kwargs={"user_id": target_user.id})
        response = self.client.patch(url, {"role": "ADMIN"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
