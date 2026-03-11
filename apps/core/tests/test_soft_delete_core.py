from django.test import TestCase
from apps.products.models import Product
from apps.vendors.models import Vendor
from django.contrib.auth import get_user_model

User = get_user_model()


class CoreSoftDeleteTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="vendor1",
            email="vendor@test.com",
            password="StrongPass123",
            role="VENDEDOR"
        )

        self.vendor = Vendor.objects.create(
            user=self.user,
            location_type="FIJA"
        )

    def create_product(self, name="TestProduct"):
        return Product.objects.create(
            name=name,
            price=10,
            stock=5,
            vendor=self.vendor
        )

    # -----------------------------------------
    # Soft delete individual
    # -----------------------------------------
    def test_soft_delete_sets_flag(self):
        product = self.create_product()

        product.delete()

        product.refresh_from_db()
        self.assertTrue(product.is_deleted)

    # -----------------------------------------
    # Default manager excludes deleted
    # -----------------------------------------
    def test_default_manager_excludes_deleted(self):
        product = self.create_product()

        product.delete()

        self.assertEqual(Product.objects.count(), 0)

    # -----------------------------------------
    # all_objects includes deleted
    # -----------------------------------------
    def test_all_objects_includes_deleted(self):
        product = self.create_product()

        product.delete()

        self.assertEqual(Product.all_objects.count(), 1)

    # -----------------------------------------
    # Restore single instance
    # -----------------------------------------
    def test_restore_instance(self):
        product = self.create_product()

        product.delete()
        product.restore()

        product.refresh_from_db()
        self.assertFalse(product.is_deleted)
        self.assertEqual(Product.objects.count(), 1)

    # -----------------------------------------
    # Hard delete removes from DB
    # -----------------------------------------
    def test_hard_delete_removes_record(self):
        product = self.create_product()

        product.hard_delete()

        self.assertEqual(Product.all_objects.count(), 0)

    # -----------------------------------------
    # Queryset soft delete
    # -----------------------------------------
    def test_queryset_soft_delete(self):
        p1 = self.create_product("A")
        p2 = self.create_product("B")

        Product.objects.all().delete()

        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Product.all_objects.count(), 2)

    # -----------------------------------------
    # Queryset restore
    # -----------------------------------------
    def test_queryset_restore(self):
        p1 = self.create_product("A")
        p2 = self.create_product("B")

        Product.objects.all().delete()
        Product.all_objects.all().restore()

        self.assertEqual(Product.objects.count(), 2)

    # -----------------------------------------
    # Double delete safe
    # -----------------------------------------
    def test_double_delete_safe(self):
        product = self.create_product()

        product.delete()
        product.delete()

        self.assertTrue(
            Product.all_objects.filter(id=product.id).exists()
        )

    # -----------------------------------------
    # Soft then hard delete
    # -----------------------------------------
    def test_soft_then_hard_delete(self):
        product = self.create_product()

        product.delete()
        product.hard_delete()

        self.assertFalse(
            Product.all_objects.filter(id=product.id).exists()
        )


    def test_soft_delete_hides_record(self):
        product = self.create_product()
        product.delete()
        self.assertFalse(Product.objects.filter(id=product.id).exists())

    def test_restore_reactivates_record(self):
        product = self.create_product()
        product.delete()
        product.restore()
        self.assertTrue(Product.objects.filter(id=product.id).exists())
