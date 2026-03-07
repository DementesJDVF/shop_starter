from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('ADMIN', 'Administrador'), ('VENDEDOR', 'Vendedor'), ('CLIENTE', 'Cliente')],
                default='CLIENTE',
                max_length=20,
            ),
        ),
    ]
