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

    def test_vendor_can_soft_delete_product(self):
        product = Product.objects.create(
            vendor=self.active_vendor,
            name="Sal",
            description="Sal fina",
            price="2.00",
            stock=10,
        )
        self.client.force_authenticate(self.vendor_user)

        response = self.client.delete(reverse("product-detail", kwargs={"product_id": product.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        product.refresh_from_db()
        self.assertTrue(product.is_deleted)
        self.assertEqual(product.status, Product.ProductStatus.INACTIVE)
        self.assertTrue(Product.all_objects.filter(id=product.id).exists())

    def test_deleted_product_not_returned_in_list(self):
        visible_product = Product.objects.create(
            vendor=self.active_vendor,
            name="Arroz",
            description="Arroz integral",
            price="4.00",
            stock=5,
        )
        deleted_product = Product.objects.create(
            vendor=self.active_vendor,
            name="Azucar",
            description="Azúcar blanca",
            price="3.00",
            stock=7,
        )
        deleted_product.is_deleted = True
        deleted_product.save(update_fields=["is_deleted", "updated_at"])

        self.client.force_authenticate(self.vendor_user)
        response = self.client.get(reverse("vendor-products"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], visible_product.id)

    def test_vendor_cannot_delete_other_vendor_product(self):
        owner_user = User.objects.create_user(
            username="owner_vendor",
            email="owner_vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        owner_vendor = Vendor.objects.create(
            user=owner_user,
            location_type=Vendor.LocationType.FIJA,
            status=Vendor.Status.ACTIVE,
        )
        product = Product.objects.create(
            vendor=owner_vendor,
            name="Aceite",
            description="Aceite de oliva",
            price="10.00",
            stock=4,
        )

        self.client.force_authenticate(self.vendor_user)
        response = self.client.delete(reverse("product-detail", kwargs={"product_id": product.id}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(str(response.data["detail"]), "You do not own this product")
        product.refresh_from_db()
        self.assertFalse(product.is_deleted)

    def test_vendor_can_patch_own_product(self):
        product = Product.objects.create(
            vendor=self.active_vendor,
            name="Galletas",
            description="Galletas de vainilla",
            price="5.00",
            stock=11,
        )

        self.client.force_authenticate(self.vendor_user)
        response = self.client.patch(
            reverse("product-detail", kwargs={"product_id": product.id}),
            {"price": "6.25"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(str(product.price), "6.25")
        self.assertEqual(product.status, Product.ProductStatus.ACTIVE)

    def test_deleted_product_cannot_be_updated(self):
        product = Product.objects.create(
            vendor=self.active_vendor,
            name="Leche",
            description="Leche deslactosada",
            price="6.00",
            stock=10,
            is_deleted=True,
        )

        self.client.force_authenticate(self.vendor_user)
        response = self.client.put(
            reverse("product-detail", kwargs={"product_id": product.id}),
            {
                "name": "Leche actualizada",
                "description": "Leche entera",
                "price": "7.00",
                "stock": 9,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
