from django.db import migrations, models


def forwards_copy_categories(apps, schema_editor):
    """
    Migra los datos de la antigua relación ForeignKey (category) a la nueva
    ManyToManyField (categories).
    """
    Product = apps.get_model('products', 'Product')
    
    # Intentamos obtener la conexión directamente para usar SQL crudo
    from django.db import connection
    cursor = connection.cursor()
    
    # Verificamos si la columna existe en la tabla (aunque Django crea que no)
    cursor.execute("PRAGMA table_info(products_product)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'category_id' not in columns:
        print("AVISO: La columna 'category_id' ya no existe en la base de datos. No se pueden migrar los datos.")
        return

    # Si existe, migramos usando SQL para evitar el FieldError del ORM
    cursor.execute("SELECT id, category_id FROM products_product WHERE category_id IS NOT NULL")
    rows = cursor.fetchall()
    
    for product_id, cat_id in rows:
        try:
            product = Product.objects.get(id=product_id)
            product.categories.add(cat_id)
        except Exception as e:
            print(f"Error migrando producto {product_id}: {e}")


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