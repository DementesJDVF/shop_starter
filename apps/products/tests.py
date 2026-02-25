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

    def create_product(self, name="Test"):
        return Product.objects.create(
            name=name,
            price=10,
            stock=5,
            vendor=self.vendor
        )

    # ------------------------------------
    # Soft delete individual
    # ------------------------------------
    def test_instance_soft_delete(self):
        product = self.create_product()

        product.delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 1)

        product.refresh_from_db()
        self.assertTrue(product.is_deleted)

    # ------------------------------------
    # Restore
    # ------------------------------------
    def test_restore(self):
        product = self.create_product()

        product.delete()
        product.restore()

        self.assertEqual(Product.objects.count(), 1)

        product.refresh_from_db()
        self.assertFalse(product.is_deleted)

    # ------------------------------------
    # Hard delete
    # ------------------------------------
    def test_hard_delete(self):
        product = self.create_product()

        product.hard_delete()

        self.assertEqual(Product.all_objects.count(), 0)

    # ------------------------------------
    # all_with_deleted
    # ------------------------------------
    def test_all_with_deleted(self):
        product = self.create_product()

        product.delete()

        self.assertEqual(Product.objects.all_with_deleted().count(), 1)

    # ------------------------------------
    # Múltiples soft deletes
    # ------------------------------------
    def test_multiple_soft_delete(self):
        p1 = self.create_product(name="A")
        p2 = self.create_product(name="B")

        p1.delete()
        p2.delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 2)

    # ------------------------------------
    # Queryset filter respeta soft delete
    # ------------------------------------
    def test_queryset_filter_excludes_deleted(self):
        product = self.create_product(name="FilterTest")

        product.delete()

        self.assertFalse(
            Product.objects.filter(name="FilterTest").exists()
        )

    # ------------------------------------
    # Restore después de múltiples deletes
    # ------------------------------------
    def test_restore_after_multiple_deletes(self):
        p1 = self.create_product(name="A")
        p2 = self.create_product(name="B")

        p1.delete()
        p2.delete()

        p1.restore()

        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(
            Product.objects.filter(name="A").exists()
        )

    def test_queryset_delete(self):
        p1 = self.create_product(name="A")
        p2 = self.create_product(name="B")

        Product.objects.all().delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 2)

    def test_queryset_restore(self):
        p1 = self.create_product(name="A")
        p2 = self.create_product(name="B")

        Product.objects.all().delete()

        Product.all_objects.all().restore()

        self.assertEqual(Product.objects.count(), 2)
        
    def test_double_delete_does_not_crash(self):
        product = self.create_product()

        product.delete()
        product.delete()  # segunda vez

        self.assertTrue(
            Product.all_objects.filter(id=product.id).exists()
        )

    def test_soft_then_hard_delete(self):
        product = self.create_product()

        product.delete()
        product.hard_delete()

        self.assertFalse(
            Product.all_objects.filter(id=product.id).exists()
        )
