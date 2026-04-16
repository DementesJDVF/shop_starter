from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.geo.models import Location
from apps.products.models import Product
from apps.reviews.models import VendorReview
from apps.users.constants import UserRoles
from apps.users.models import User


class VendorReviewEndpointTests(APITestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(
            username="vendor-user",
            email="vendor@example.com",
            password="secret123",
            role=UserRoles.VENDEDOR,
            status=User.Status.ACTIVE,
        )
        self.customer = User.objects.create_user(
            username="customer-user",
            email="customer@example.com",
            password="secret123",
            role=UserRoles.CLIENTE,
            status=User.Status.ACTIVE,
        )
        self.location = Location.objects.create(
            user=self.customer,
            latitude=10.0,
            longitude=10.0,
            description="Test location",
        )
        self.product = Product.objects.create(
            vendor=self.vendor,
            name="Fresh Fruit Basket",
            description="A healthy selection of fruit.",
            price=100.00,
            stock=10,
            status=Product.ProductStatus.ACTIVE,
        )
        self.url = reverse("vendor-review", kwargs={"vendor_id": self.vendor.id})

    def test_post_creates_vendor_review_for_completed_order(self):
        # REMOVED: Order setup is no longer required for review submission.
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(self.url, {"rating": 5, "review_text": "Great seller"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["client"], self.customer.username)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(VendorReview.objects.count(), 1)

    def test_post_updates_existing_vendor_review(self):
        # REMOVED: Order setup is no longer required for review updates.
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(self.url, {"rating": 4, "review_text": "Good"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(self.url, {"rating": 3, "review_text": "Okay"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(VendorReview.objects.count(), 1)
        review = VendorReview.objects.first()
        self.assertEqual(review.rating, 3)
        self.assertEqual(review.review_text, "Okay")

    def test_get_returns_vendor_review_summary(self):
        second_customer = User.objects.create_user(
            username="customer-user-2",
            email="customer2@example.com",
            password="secret123",
            role=UserRoles.CLIENTE,
            status=User.Status.ACTIVE,
        )

        # REMOVED: Order setup is no longer required for vendor review summary tests.
        VendorReview.objects.create(
            vendor=self.vendor,
            client=self.customer,
            rating=5,
            review_text="Nice",
        )
        VendorReview.objects.create(
            vendor=self.vendor,
            client=second_customer,
            rating=4,
            review_text="Good",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average"], 4.5)
        self.assertEqual(response.data["total"], 2)
        self.assertEqual(len(response.data["reviews"]), 2)
