import importlib
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.geo.models import Location
from apps.users.constants import UserRoles
from apps.users.models import User


class Command(BaseCommand):
    help = "Load development test data for vendor users, locations, and products."

    def handle(self, *args, **options):
        vendor_profile_model = self._load_vendor_profile_model()
        category_model, product_model = self._load_product_models()

        vendor_definitions = [
            {
                "email": "vendor_test1@shopstarter.com",
                "username": "vendor_test1",
                "password": "Test1234!",
                "location": {
                    "latitude": Decimal("2.4448"),
                    "longitude": Decimal("-76.6147"),
                    "description": "Popayán, Colombia",
                },
                "products": [
                    {
                        "name": "Popayán Coffee Beans",
                        "description": "Premium roasted coffee from Popayán.",
                        "price": Decimal("25.00"),
                    },
                    {
                        "name": "Popayán Artisan Chocolate",
                        "description": "Handmade chocolate from local cocoa.",
                        "price": Decimal("18.50"),
                    },
                ],
            },
            {
                "email": "vendor_test2@shopstarter.com",
                "username": "vendor_test2",
                "password": "Test1234!",
                "location": {
                    "latitude": Decimal("2.4419"),
                    "longitude": Decimal("-76.6079"),
                    "description": "Popayán, Colombia",
                },
                "products": [
                    {
                        "name": "Popayán Pastry Box",
                        "description": "A selection of fresh pastries from Popayán.",
                        "price": Decimal("15.00"),
                    },
                    {
                        "name": "Popayán Ceramic Mug",
                        "description": "Locally crafted ceramic mug from Popayán artisans.",
                        "price": Decimal("22.00"),
                    },
                ],
            },
        ]

        with transaction.atomic():
            for vendor_data in vendor_definitions:
                user = self._create_or_update_vendor_user(vendor_data)
                self._create_vendor_profile(user, vendor_profile_model)
                self._create_vendor_location(user, vendor_data["location"])
                self._create_vendor_products(user, category_model, product_model, vendor_data["products"])

        self.stdout.write(self.style.SUCCESS("Test data load complete."))

    def _load_vendor_profile_model(self):
        try:
            module = importlib.import_module("apps.vendors.models")
        except ModuleNotFoundError:
            self.stdout.write(self.style.WARNING("apps.vendors.models module not found. Skipping VendorProfile creation."))
            return None

        vendor_profile_model = getattr(module, "VendorProfile", None)
        if vendor_profile_model is None:
            self.stdout.write(self.style.WARNING("VendorProfile model not found in apps.vendors.models. Skipping VendorProfile creation."))
        return vendor_profile_model

    def _load_product_models(self):
        try:
            from apps.products.models import Category, Product

            return Category, Product
        except ImportError as exc:
            self.stdout.write(self.style.WARNING(f"Could not import product models: {exc}. Skipping product creation."))
            return None, None

    def _create_or_update_vendor_user(self, vendor_data):
        defaults = {
            "username": vendor_data["username"],
            "role": UserRoles.VENDEDOR,
            "status": User.Status.ACTIVE,
        }
        user, created = User.objects.get_or_create(email=vendor_data["email"], defaults=defaults)

        if created:
            user.set_password(vendor_data["password"])
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created vendor user {user.email}."))
        else:
            changed = False
            if user.username != defaults["username"]:
                user.username = defaults["username"]
                changed = True
            if user.role != defaults["role"]:
                user.role = defaults["role"]
                changed = True
            if user.status != defaults["status"]:
                user.status = defaults["status"]
                changed = True
            if changed:
                user.save(update_fields=[field for field in ["username", "role", "status"] if getattr(user, field) == defaults[field]])
                self.stdout.write(self.style.SUCCESS(f"Updated vendor user {user.email}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Vendor user {user.email} already exists."))

        return user

    def _create_vendor_profile(self, user, vendor_profile_model):
        if vendor_profile_model is None:
            return

        defaults = {}
        if self._model_has_field(vendor_profile_model, "status"):
            defaults["status"] = User.Status.ACTIVE

        try:
            profile, created = vendor_profile_model.objects.get_or_create(user=user, defaults=defaults)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created VendorProfile for {user.email}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"VendorProfile for {user.email} already exists."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Skipping VendorProfile creation for {user.email}: {exc}"))

    def _create_vendor_location(self, user, location_data):
        try:
            location, created = Location.objects.update_or_create(
                user=user,
                defaults={
                    "latitude": location_data["latitude"],
                    "longitude": location_data["longitude"],
                    "description": location_data.get("description", ""),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created location for {user.email}."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated location for {user.email}."))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Skipping location creation for {user.email}: {exc}"))

    def _create_vendor_products(self, user, category_model, product_model, products):
        if product_model is None:
            return

        category = None
        if category_model is not None:
            category, _ = category_model.objects.get_or_create(
                name="Test Products",
                defaults={
                    "description": "Products used for development testing.",
                    "emoji": "🛒" if self._model_has_field(category_model, "emoji") else None,
                    "is_active": True if self._model_has_field(category_model, "is_active") else None,
                },
            )
            if category is not None:
                self.stdout.write(self.style.SUCCESS("Ensured test product category exists."))

        for product_data in products:
            defaults = {
                "description": product_data["description"],
                "price": product_data["price"],
                "stock": 10,
                "status": product_model.ProductStatus.ACTIVE if self._model_has_field(product_model, "status") else None,
            }
            if category is not None and self._model_has_field(product_model, "category"):
                defaults["category"] = category

            defaults = {k: v for k, v in defaults.items() if v is not None}

            try:
                product, created = product_model.objects.get_or_create(
                    vendor=user,
                    name=product_data["name"],
                    defaults=defaults,
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created product {product.name} for {user.email}."))
                else:
                    changed = False
                    for field, value in defaults.items():
                        if getattr(product, field, None) != value:
                            setattr(product, field, value)
                            changed = True
                    if changed:
                        product.save()
                        self.stdout.write(self.style.SUCCESS(f"Updated product {product.name} for {user.email}."))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"Product {product.name} for {user.email} already exists."))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"Skipping product {product_data['name']} for {user.email}: {exc}"))

    def _model_has_field(self, model, field_name):
        try:
            model._meta.get_field(field_name)
            return True
        except Exception:
            return False
