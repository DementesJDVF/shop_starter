
import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.products.models import Product, PImages

print("--- Products ---")
for p in Product.objects.all():
    print(f"ID: {p.id}, Name: {p.name}")

print("\n--- Images ---")
for img in PImages.objects.all():
    try:
        print(f"ID: {img.id}, Product ID: {img.product_id}, Product: {img.product.name}")
    except Exception as e:
        print(f"ID: {img.id}, Product ID: {img.product_id}, ERROR: {e}")
