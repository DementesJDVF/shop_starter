"""Tests for category API endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Category
from apps.users.models import User


class CategoryApiTests(APITestCase):
    """Validate category list/create behavior."""

    def setUp(self):
        self.list_url = reverse("categories-list")
        self.user = User.objects.create_user(
            username="catalog_tester",
            email="catalog_tester@example.com",
            password="secure-pass-123",
            role="ADMIN",
        )
        self.client.force_authenticate(self.user)

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
        first_response = self.client.post(self.list_url, {"name": "Aseo"}, format="json")
        second_response = self.client.post(self.list_url, {"name": "Panadería"}, format="json")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data]
        self.assertEqual(result_ids, [first_response.data["id"], second_response.data["id"]])

    def test_retrieve_category_by_id(self):
        create_response = self.client.post(self.list_url, {"name": "Tecnología"}, format="json")
        category_id = create_response.data["id"]

        response = self.client.get(reverse("categories-detail", kwargs={"category_id": category_id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], category_id)
        self.assertEqual(response.data["name"], "Tecnología")