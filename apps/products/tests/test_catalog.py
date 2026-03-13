"""Tests for public catalog endpoint."""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Product
from apps.users.models import User
from apps.vendors.models import Vendor


class CatalogViewTests(APITestCase):
    """Validate public catalog behavior and filters."""

    def setUp(self):
        self.url = reverse("catalog-list")

        self.active_vendor_user = User.objects.create_user(
            username="active_vendor",
            email="active_vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        self.active_vendor = Vendor.objects.create(
            user=self.active_vendor_user,
            location_type=Vendor.LocationType.FIJA,
            status=Vendor.Status.ACTIVE,
        )

        self.inactive_vendor_user = User.objects.create_user(
            username="inactive_vendor",
            email="inactive_vendor@example.com",
            password="secure-pass-123",
            role="VENDEDOR",
        )
        self.inactive_vendor = Vendor.objects.create(
            user=self.inactive_vendor_user,
            location_type=Vendor.LocationType.MOVIL,
            status=Vendor.Status.BLOCKED,
        )

    def _create_product(self, **kwargs):
        defaults = {
            "vendor": self.active_vendor,
            "name": "Producto",
            "description": "Descripción",
            "price": "10.00",
            "stock": 1,
            "status": Product.ProductStatus.ACTIVE,
            "is_deleted": False,
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    def test_catalog_returns_only_active_products(self):
        visible_product = self._create_product(name="Visible")
        self._create_product(name="Borrador", status=Product.ProductStatus.DRAFT)
        self._create_product(name="Eliminado", is_deleted=True)
        self._create_product(
            name="Vendedor bloqueado",
            vendor=self.inactive_vendor,
            status=Product.ProductStatus.ACTIVE,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], visible_product.id)

    def test_catalog_is_public_without_authentication(self):
        self._create_product(name="Visible")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_catalog_search_by_name(self):
        product = self._create_product(name="Zapato runner", description="Calzado")
        self._create_product(name="Camisa", description="Ropa")

        response = self.client.get(self.url, {"search": "runner"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], product.id)

    def test_catalog_search_by_description(self):
        product = self._create_product(name="Tenis", description="Zapato deportivo")
        self._create_product(name="Sandalia", description="Calzado fresco")

        response = self.client.get(self.url, {"search": "deportivo"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], product.id)

    def test_catalog_response_is_paginated(self):
        for index in range(11):
            self._create_product(name=f"Producto {index}")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)

    def test_catalog_ordering_by_price(self):
        self._create_product(name="B", price="30.00")
        self._create_product(name="A", price="10.00")

        response = self.client.get(self.url, {"ordering": "price"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["price"], "10.00")
        self.assertEqual(response.data["results"][1]["price"], "30.00")

    def test_catalog_ordering_by_created_at(self):
        old_product = self._create_product(name="Viejo")
        new_product = self._create_product(name="Nuevo")

        Product.all_objects.filter(id=old_product.id).update(created_at=timezone.now() - timedelta(days=2))
        Product.all_objects.filter(id=new_product.id).update(created_at=timezone.now() - timedelta(days=1))

        response = self.client.get(self.url, {"ordering": "created_at"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(result_ids[:2], [old_product.id, new_product.id])
