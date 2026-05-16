from django.db import migrations


def forwards_copy_categories(apps, schema_editor):
    """
    Migrar los datos de la antigua relación ForeignKey (category) a la nueva
    ManyToManyField (categories). Funciona con cualquier backend de base de datos.
    """
    Product = apps.get_model('products', 'Product')
    
    # Usamos el ORM directamente - es backend-agnostic
    # Solo procesamos productos que tengan category_id (no None/null)
    for product in Product.objects.exclude(category__isnull=True).iterator():
        try:
            product.categories.add(product.category_id)
        except Exception as e:
            print(f"Error migrando producto {product.id}: {e}")


def backwards_noop(apps, schema_editor):
    """No se puede revertir la pérdida de datos de M2M a FK automáticamente."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_product_categories_m2m'),
    ]

    operations = [
        migrations.RunPython(forwards_copy_categories, backwards_noop),
    ]