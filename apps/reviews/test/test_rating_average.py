from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Order
from apps.reviews.models import Review
from apps.users.constants import UserRoles
from apps.users.models import User
from apps.vendors.models import VendorProfile


class VendorRatingQuerySetTests(TestCase):
    """Validates dynamic reputation annotations for vendor profiles."""

    def setUp(self):
        self.vendor_user = User.objects.create_user(
            username="frutas-don-pedro",
            email="vendor@example.com",
            password="secret123",
            role=UserRoles.VENDEDOR,
        )
        self.customer = User.objects.create_user(
            username="customer-1",
            email="customer@example.com",
            password="secret123",
            role=UserRoles.CLIENTE,
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            location_type=VendorProfile.LocationType.FIXED,
            status=VendorProfile.Status.ACTIVE,
        )

    def test_average_rating(self):
        first_order = Order.objects.create(client=self.customer, vendor=self.vendor)
        second_order = Order.objects.create(client=self.customer, vendor=self.vendor)

        Review.objects.create(order=first_order, client=self.customer, vendor=self.vendor, rating=4)
        Review.objects.create(order=second_order, client=self.customer, vendor=self.vendor, rating=5)

        rated_vendor = VendorProfile.objects.with_rating().get(pk=self.vendor.pk)

        self.assertEqual(rated_vendor.average_rating, 4.5)
        self.assertEqual(rated_vendor.total_reviews, 2)

    def test_vendor_without_reviews(self):
        unrated_vendor = VendorProfile.objects.with_rating().get(pk=self.vendor.pk)

        self.assertIsNone(unrated_vendor.average_rating)
        self.assertEqual(unrated_vendor.total_reviews, 0)


class VendorPublicEndpointRatingTests(APITestCase):
    def test_public_endpoint_returns_rounded_average_and_total_reviews(self):
        vendor_user = User.objects.create_user(
            username="Frutas Don Pedro",
            email="vendor2@example.com",
            password="secret123",
            role=UserRoles.VENDEDOR,
        )
        customer = User.objects.create_user(
            username="customer-2",
            email="customer2@example.com",
            password="secret123",
            role=UserRoles.CLIENTE,
        )
        vendor = VendorProfile.objects.create(
            user=vendor_user,
            status=VendorProfile.Status.ACTIVE,
            location_type=VendorProfile.LocationType.FIXED,
        )

        ratings = [5, 4, 5]
        for index, value in enumerate(ratings, start=1):
            order = Order.objects.create(client=customer, vendor=vendor)
            Review.objects.create(
                order=order,
                client=customer,
                vendor=vendor,
                rating=value,
                comment=f"review-{index}",
            )

        response = self.client.get(reverse("vendor-public-detail", kwargs={"id": vendor.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(vendor.id))
        self.assertEqual(response.data["business_name"], "Frutas Don Pedro")
        self.assertEqual(response.data["average_rating"], 4.67)
        self.assertEqual(response.data["total_reviews"], 3)