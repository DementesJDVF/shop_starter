from rest_framework.test import APITestCase
from django.urls import reverse
from apps.users.models import User
from apps.vendors.models import VendorProfile


class VendorProfileCreationTests(APITestCase):

    def setUp(self):
        self.vendor = User.objects.create_user(
            email="vendor@test.com",
            password="123456",
            role=User.Role.VENDOR
        )

    def authenticate(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": user.email, "password": "123456"}
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )

    def test_vendor_can_create_profile(self):
        self.authenticate(self.vendor)

        response = self.client.post(
            reverse("vendor-profile-create"),
            {"location_type": "FIXED"}
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(VendorProfile.objects.count(), 1)

    def test_duplicate_profile_not_allowed(self):
        self.authenticate(self.vendor)

        self.client.post(
            reverse("vendor-profile-create"),
            {"location_type": "FIXED"}
        )

        response = self.client.post(
            reverse("vendor-profile-create"),
            {"location_type": "FIXED"}
        )

        self.assertEqual(response.status_code, 400)