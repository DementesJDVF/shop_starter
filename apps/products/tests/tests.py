"""Unit tests for Product model soft-delete behavior."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.products.models import Product
from apps.vendors.models import Vendor

User = get_user_model()


class ProductSoftDeleteTestCase(TestCase):
    """Validate Product soft-delete lifecycle and queryset helpers."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor1",
            email="vendor@test.com",
            password="123456",
            role="VENDEDOR",
        )
        self.vendor = Vendor.objects.create(
            user=self.user,
            location_type=Vendor.LocationType.FIJA,
            status=Vendor.Status.ACTIVE,
        )

    def create_product(self, *, name: str = "Test", price: str = "10.00", stock: int = 5) -> Product:
        """Factory helper for Product instances used in tests."""
        return Product.objects.create(
            name=name,
            description=f"Descripción de {name}",
            price=price,
            stock=stock,
            vendor=self.vendor,
        )

    def test_instance_soft_delete_marks_record_and_hides_from_default_manager(self):
        product = self.create_product()

        product.delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 1)
        product.refresh_from_db()
        self.assertTrue(product.is_deleted)

    def test_restore_returns_soft_deleted_record_to_default_manager(self):
        product = self.create_product()
        product.delete()

        product.restore()

        self.assertEqual(Product.objects.count(), 1)
        product.refresh_from_db()
        self.assertFalse(product.is_deleted)

    def test_hard_delete_removes_row_from_database(self):
        product = self.create_product()

        product.hard_delete()

        self.assertEqual(Product.all_objects.count(), 0)

    def test_all_with_deleted_includes_deleted_rows(self):
        product = self.create_product()
        product.delete()

        self.assertEqual(Product.objects.all_with_deleted().count(), 1)

    def test_queryset_delete_soft_deletes_all_rows(self):
        self.create_product(name="A")
        self.create_product(name="B")

        Product.objects.all().delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 2)

    def test_queryset_restore_recovers_soft_deleted_rows(self):
        self.create_product(name="A")
        self.create_product(name="B")
        Product.objects.all().delete()

        Product.all_objects.all().restore()

        self.assertEqual(Product.objects.count(), 2)

    def test_filter_excludes_deleted_records(self):
        product = self.create_product(name="FilterTest")
        product.delete()

        self.assertFalse(Product.objects.filter(name="FilterTest").exists())

    def test_restore_after_multiple_soft_deletes_recovers_only_target(self):
        product_a = self.create_product(name="A")
        self.create_product(name="B")
        Product.objects.all().delete()

        product_a.restore()

        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(Product.objects.filter(name="A").exists())

    def test_double_soft_delete_is_idempotent(self):
        product = self.create_product()

        product.delete()
        product.delete()

        self.assertTrue(Product.all_objects.filter(id=product.id).exists())

    def test_soft_delete_then_hard_delete_removes_row(self):
        product = self.create_product()
        product.delete()

        product.hard_delete()

        self.assertFalse(Product.all_objects.filter(id=product.id).exists())
