import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0003_alter_order_options_alter_order_client_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name="order",
            old_name="client",
            new_name="customer",
        ),
        migrations.AlterField(
            model_name="order",
            name="customer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="customer_orders",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("CREADO", "Creado"),
                    ("CONFIRMADO", "Confirmado"),
                    ("COMPLETADO", "Completado"),
                    ("CANCELADO", "Cancelado"),
                ],
                db_index=True,
                default="CREADO",
                max_length=20,
            ),
        ),
        migrations.RenameField(
            model_name="orderitem",
            old_name="price_at_purchase",
            new_name="price",
        ),
        migrations.AddField(
            model_name="orderitem",
            name="subtotal",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.RemoveIndex(
            model_name="order",
            name="orders_orde_client__7a26db_idx",
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["customer"], name="orders_orde_custome_7a26db_idx"),
        ),
    ]