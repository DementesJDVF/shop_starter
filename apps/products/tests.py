from django.test import TestCase
from apps.products.models import Product
from apps.vendors.models import Vendor
from django.contrib.auth import get_user_model


User = get_user_model()


class SoftDeleteTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor1",
            email="vendor@test.com",
            password="123456",
            role="VENDOR"
        )

        self.vendor = Vendor.objects.create(
            user=self.user,
            location_type="FIJA"
        )

    def test_instance_soft_delete(self):
        product = Product.objects.create(
            name="Test",
            price=10,
            stock=5,
            vendor=self.vendor
        )

        product.delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 1)
        self.assertTrue(Product.all_objects.first().is_deleted)

    def test_restore(self):
        product = Product.objects.create(
            name="Test",
            price=10,
            stock=5,
            vendor=self.vendor
        )

        product.delete()
        product.restore()

        self.assertEqual(Product.objects.count(), 1)
        self.assertFalse(Product.objects.first().is_deleted)
