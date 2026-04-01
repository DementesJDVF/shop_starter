"""Tests for category API endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category


class CategoryApiTests(APITestCase):
    """Validate category list/create behavior."""

    def setUp(self):
        self.list_url = reverse("categories-list")

    def test_can_create_category_with_trailing_slash(self):
        payload = {"name": "Verduras"}

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.first().name, "Verduras")

    def test_can_create_category_without_trailing_slash(self):
        payload = {"name": "Bebidas"}

        response = self.client.post("/api/products/categories", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name="Bebidas").exists())

    def test_list_categories_returns_created_items(self):
        first = Category.objects.create(name="Aseo")
        second = Category.objects.create(name="Panadería")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data]
        self.assertEqual(result_ids, [first.id, second.id])