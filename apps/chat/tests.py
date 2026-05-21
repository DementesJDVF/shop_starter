from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.products.models import Product, Category

class ChatAssistantTests(APITestCase):
    def setUp(self):
        # Create a vendor user
        self.vendor = User.objects.create_user(
            username='vendoruser',
            email='vendor@example.com',
            password='Password123!',
            role='VENDEDOR'
        )
        
        # Create a category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            emoji='🧪'
        )
        
        # Create a product
        self.product = Product.objects.create(
            vendor=self.vendor,
            name='Super Blue Widget',
            description='A widget that is super blue',
            price=29.99,
            stock=10,
            status='AVAILABLE'
        )
        self.product.categories.add(self.category)
        
        self.chat_url = reverse('chat_assistant')

    def test_chat_assistant_keywords_matching(self):
        """Test chat assistant with matching keyword in category name"""
        data = {
            'message': 'Necesito algo de la categoría Test Category'
        }
        response = self.client.post(self.chat_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The product should be in the returned list of products
        product_ids = [p['id'] for p in response.data['products']]
        self.assertIn(str(self.product.id), product_ids)

    def test_chat_assistant_no_matching(self):
        """Test chat assistant with no matching keywords"""
        data = {
            'message': 'Quiero un elefante volador'
        }
        response = self.client.post(self.chat_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['products']), 0)
