import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.products.models import Category

count = Category.objects.count()
print(f"Total categories: {count}")
for cat in Category.objects.all():
    print(f"- {cat.id}: {cat.name} (active: {cat.is_active}, deleted: {cat.is_deleted})")
