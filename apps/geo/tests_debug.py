from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.geo.models import Location
from rest_framework import status

User = get_user_model()

class GeoErrorTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="test@example.com", username="testuser", password="Password123!")
        self.client.force_authenticate(user=self.user)

    def test_my_location_no_location(self):
        response = self.client.get("/api/geo/my-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_my_location_with_location(self):
        Location.objects.create(user=self.user, latitude=1.23, longitude=4.56, description="Test")
        response = self.client.get("/api/geo/my-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
