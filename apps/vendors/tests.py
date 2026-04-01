from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.constants import UserRoles
from apps.users.models import User
from apps.vendors.models import VendorProfile
from apps.vendors.selectors import VendorSelectors


class VendorCreationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor1",
            email="vendor@test.com",
            password="123456",
            role=UserRoles.VENDEDOR,
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin@test.com",
            password="123456",
            role=UserRoles.ADMIN,
        )

    def authenticate(self, user):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": user.email, "password": "123456"},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_vendor_can_create(self):
        self.authenticate(self.user)

        response = self.client.post(reverse("vendor-create"), {"location_type": "FIXED"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VendorProfile.objects.count(), 1)

    def test_duplicate_vendor_not_allowed(self):
        self.authenticate(self.user)

        self.client.post(reverse("vendor-create"), {"location_type": "FIXED"})

        response = self.client.post(reverse("vendor-create"), {"location_type": "FIXED"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vendor_can_update_profile(self):
        self.authenticate(self.user)

        self.client.post(reverse("vendor-create"), {"location_type": "FIXED"})

        response = self.client.patch(
            reverse("vendor-me"),
            {"location_type": "MOBILE"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location_type"], "MOBILE")

    def test_non_vendor_cannot_create(self):
        self.user.role = UserRoles.CLIENTE
        self.user.save()
        self.authenticate(self.user)

        response = self.client.post(reverse("vendor-create"), {"location_type": "FIXED"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_vendor_by_user(self):
        profile = VendorProfile.objects.create(user=self.user, location_type="FIXED")

        result = VendorSelectors.get_vendor_profile_by_user(self.user)
        self.assertEqual(result.id, profile.id)

    def test_private_endpoints_require_authentication(self):
        create_response = self.client.post(
            reverse("vendor-create"),
            {"location_type": "FIXED"},
        )
        me_response = self.client.get(reverse("vendor-me"))

        self.assertEqual(create_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(me_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_vendor_can_get_own_profile(self):
        self.authenticate(self.user)
        VendorProfile.objects.create(user=self.user, location_type="FIXED")

        response = self.client.get(reverse("vendor-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location_type"], "FIXED")

    def test_public_detail_only_returns_active_and_verified_profiles(self):
        active_profile = VendorProfile.objects.create(
            user=self.user,
            location_type="FIXED",
            status=VendorProfile.Status.ACTIVE,
            verified=True,
        )

        inactive_user = User.objects.create_user(
            username="vendor2",
            email="vendor2@test.com",
            password="123456",
            role=UserRoles.VENDEDOR,
        )
        inactive_profile = VendorProfile.objects.create(
            user=inactive_user,
            location_type="FIXED",
            status=VendorProfile.Status.PENDING,
            verified=False,
        )

        ok_response = self.client.get(
            reverse("vendor-public-detail", kwargs={"vendor_id": active_profile.id})
        )
        not_found_response = self.client.get(
            reverse("vendor-public-detail", kwargs={"vendor_id": inactive_profile.id})
        )

        self.assertEqual(ok_response.status_code, status.HTTP_200_OK)
        self.assertEqual(not_found_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_only_fields_cannot_be_updated_by_vendor(self):
        self.authenticate(self.user)
        VendorProfile.objects.create(user=self.user, location_type="FIXED")

        response = self.client.patch(
            reverse("vendor-me"),
            {"status": VendorProfile.Status.ACTIVE, "verified": True, "reputation": "5.00"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], VendorProfile.Status.PENDING)
        self.assertEqual(response.data["verified"], False)
        self.assertEqual(response.data["reputation"], "0.00")


    def test_admin_can_moderate_vendor_status_and_verification(self):
        profile = VendorProfile.objects.create(user=self.user, location_type="FIXED")
        self.authenticate(self.admin)

        response = self.client.patch(
            reverse("vendor-moderation", kwargs={"vendor_id": profile.id}),
            {"status": VendorProfile.Status.ACTIVE, "verified": True},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], VendorProfile.Status.ACTIVE)
        self.assertEqual(response.data["verified"], True)

    def test_non_admin_cannot_moderate_vendor(self):
        profile = VendorProfile.objects.create(user=self.user, location_type="FIXED")
        self.authenticate(self.user)

        response = self.client.patch(
            reverse("vendor-moderation", kwargs={"vendor_id": profile.id}),
            {"status": VendorProfile.Status.ACTIVE, "verified": True},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_verify_vendor_if_not_active(self):
        profile = VendorProfile.objects.create(user=self.user, location_type="FIXED")
        self.authenticate(self.admin)

        response = self.client.patch(
            reverse("vendor-moderation", kwargs={"vendor_id": profile.id}),
            {"status": VendorProfile.Status.PENDING, "verified": True},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
