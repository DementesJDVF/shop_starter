from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Order
from apps.products.models import Category, Product
from apps.users.models import User
from apps.vendors.models import VendorProfile


class CreateOrderTests(APITestCase):
    def setUp(self):
        self.url = reverse("create-order")

        self.customer = User.objects.create_user(
            username="cliente",
            email="cliente@example.com",
            password="password123",
            role="CLIENTE",
        )

        self.vendor_user = User.objects.create_user(
            username="vendor",
            email="vendor@example.com",
            password="password123",
            role="VENDEDOR",
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            status=VendorProfile.Status.ACTIVE,
            location_type=VendorProfile.LocationType.FIXED,
        )

        self.other_vendor_user = User.objects.create_user(
            username="vendor2",
            email="vendor2@example.com",
            password="password123",
            role="VENDEDOR",
        )
        self.other_vendor = VendorProfile.objects.create(
            user=self.other_vendor_user,
            status=VendorProfile.Status.ACTIVE,
            location_type=VendorProfile.LocationType.FIXED,
        )

        self.category = Category.objects.create(name="Granos")

        self.product_1 = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Arroz",
            description="Arroz premium",
            price=Decimal("5.00"),
            stock=10,
            status=Product.ProductStatus.ACTIVE,
        )
        self.product_2 = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Frijol",
            description="Frijol rojo",
            price=Decimal("7.50"),
            stock=5,
            status=Product.ProductStatus.ACTIVE,
        )

    def authenticate(self):
        self.client.force_authenticate(self.customer)

    def test_create_order_success(self):
        self.authenticate()
        payload = {
            "items": [
                {"product_id": str(self.product_1.id), "quantity": 2},
                {"product_id": str(self.product_2.id), "quantity": 1},
            ]
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.get()
        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.vendor, self.vendor)
        self.assertEqual(order.status, Order.Status.CREATED)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total, Decimal("17.50"))

    def test_reject_unauthenticated_user(self):
        payload = {"items": [{"product_id": str(self.product_1.id), "quantity": 1}]}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reject_inactive_products(self):
        self.authenticate()
        self.product_1.status = Product.ProductStatus.INACTIVE
        self.product_1.save(update_fields=["status", "updated_at"])

        payload = {"items": [{"product_id": str(self.product_1.id), "quantity": 1}]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_blocked_vendor(self):
        self.authenticate()
        self.vendor.status = VendorProfile.Status.BLOCKED
        self.vendor.save(update_fields=["status", "updated_at"])

        payload = {"items": [{"product_id": str(self.product_1.id), "quantity": 1}]}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_products_from_different_vendors(self):
        self.authenticate()
        product_other_vendor = Product.objects.create(
            vendor=self.other_vendor,
            category=self.category,
            name="Azucar",
            description="Azucar morena",
            price=Decimal("3.00"),
            stock=10,
            status=Product.ProductStatus.ACTIVE,
        )

        payload = {
            "items": [
                {"product_id": str(self.product_1.id), "quantity": 1},
                {"product_id": str(product_other_vendor.id), "quantity": 1},
            ]
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_when_stock_is_insufficient(self):
        self.authenticate()
        payload = {"items": [{"product_id": str(self.product_2.id), "quantity": 10}]}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_validate_empty_order(self):
        self.authenticate()

        response = self.client.post(self.url, {"items": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_total_is_calculated_in_backend(self):
        self.authenticate()
        payload = {
            "items": [{"product_id": str(self.product_1.id), "quantity": 3}],
            "total": "1.00",
            "vendor": str(self.other_vendor.id),
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        self.assertEqual(order.total, Decimal("15.00"))
        self.assertNotEqual(str(order.vendor.id), str(self.other_vendor.id))