from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.vendors.models import Vendor
from apps.vendors.selectors import VendorSelectors


class VendorCreationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor1",
            email="vendor@test.com",
            password="123456",
            role=User.Role.VENDEDOR
        )

    def authenticate(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": user.email, "password": "123456"}
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_vendor_can_create(self):
        self.authenticate(self.user)

        response = self.client.post(
            reverse("vendor-list"),
            {"location_type": "FIXED"}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vendor.objects.count(), 1)

    def test_duplicate_vendor_not_allowed(self):
        self.authenticate(self.user)

        self.client.post(
            reverse("vendor-list"),
            {"location_type": "FIXED"}
        )

        response = self.client.post(
            reverse("vendor-list"),
            {"location_type": "FIXED"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendor_can_update_profile(self):
        self.authenticate(self.user)

        # Crear primero
        self.client.post(
            reverse("vendor-list"),
            {"location_type": "FIXED"}
        )

        # Actualizar usando endpoint /me/
        response = self.client.patch(
            reverse("vendor-detail"),
            {"location_type": "MOBILE"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location_type"], "MOBILE")

    def test_non_vendor_cannot_create(self):
        # Cambiar a cualquier rol diferente a VENDEDOR
        for role in User.Role:
            if role != User.Role.VENDEDOR:
                self.user.role = role
                break

        self.user.save()
        self.authenticate(self.user)

        response = self.client.post(
            reverse("vendor-list"),
            {"location_type": "FIXED"}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_vendor_by_user(self):
        profile = Vendor.objects.create(
            user=self.user,
            location_type="FIXED"
        )

        result = VendorSelectors.get_vendor_profile_by_user(self.user)
        self.assertEqual(result.id, profile.id)