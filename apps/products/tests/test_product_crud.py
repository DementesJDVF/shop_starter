"""API integration tests for product CRUD endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Product
from apps.users.models import User
from apps.vendors.models import Vendor


class ProductCrudTests(APITestCase):
    """Validate product CRUD business rules through API."""

    def setUp(self):
        self.vendor_user = User.objects.create_user(
            username="vendor_user",
            email="vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        self.active_vendor = Vendor.objects.create(
            user=self.vendor_user,
            location_type=Vendor.LocationType.FIJA,
            status=Vendor.Status.ACTIVE,
        )
        self.create_url = reverse("product-create")

    def test_create_product_success(self):
        self.client.force_authenticate(self.vendor_user)

        payload = {
            "name": "Arroz Premium",
            "description": "Arroz blanco de 1kg",
            "price": "5.50",
            "stock": 20,
        }

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

        product = Product.objects.get()
        self.assertEqual(product.vendor, self.active_vendor)
        self.assertEqual(product.status, Product.Status.DRAFT)

    def test_create_product_error_when_price_is_not_positive(self):
        self.client.force_authenticate(self.vendor_user)

        payload = {
            "name": "Azúcar",
            "description": "Bolsa de azúcar",
            "price": "0",
            "stock": 3,
        }

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)

    def test_create_product_error_when_user_is_not_vendor(self):
        client_user = User.objects.create_user(
            username="client_user",
            email="client@example.com",
            password="secure-pass-123",
            role="CLIENTE",
        )
        self.client.force_authenticate(client_user)

        payload = {
            "name": "Pan",
            "description": "Pan tajado",
            "price": "3.00",
            "stock": 8,
        }

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(str(response.data["detail"]), "Only vendor users can manage products")

    def test_create_product_error_when_vendor_is_not_active(self):
        inactive_vendor_user = User.objects.create_user(
            username="pending_vendor",
            email="pending_vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        Vendor.objects.create(
            user=inactive_vendor_user,
            location_type=Vendor.LocationType.MOVIL,
            status=Vendor.Status.PENDING,
        )
        self.client.force_authenticate(inactive_vendor_user)

        payload = {
            "name": "Frijol",
            "description": "Frijol rojo",
            "price": "4.20",
            "stock": 10,
        }

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["detail"]), "Vendor profile must be active")

    def test_only_owner_can_update_product(self):
        product = Product.objects.create(
            vendor=self.active_vendor,
            name="Aceite",
            description="Aceite vegetal",
            price="8.50",
            stock=5,
        )

        other_vendor_user = User.objects.create_user(
            username="other_vendor",
            email="other_vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        Vendor.objects.create(
            user=other_vendor_user,
            location_type=Vendor.LocationType.FIJA,
            status=Vendor.Status.ACTIVE,
        )

        self.client.force_authenticate(other_vendor_user)
        response = self.client.put(
            reverse("product-detail", kwargs={"product_id": product.id}),
            {
                "name": "Aceite actualizado",
                "description": "Aceite vegetal x2",
                "price": "9.00",
                "stock": 6,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(str(response.data["detail"]), "You do not own this product")

    def test_create_product_requires_authentication(self):
        payload = {
            "name": "Harina",
            "description": "Harina de trigo",
            "price": "2.50",
            "stock": 12,
        }

        response = self.client.post(self.create_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product_validates_required_fields(self):
        self.client.force_authenticate(self.vendor_user)

        response = self.client.post(self.create_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("description", response.data)
        self.assertIn("price", response.data)
