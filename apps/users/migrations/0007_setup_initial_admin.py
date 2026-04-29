from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_initial_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    email = "neythanayala670@gmail.com"
    username = "neythan_admin"
    password = "AdminShop2026*"

    if not User.objects.filter(email=email).exists():
        User.objects.create(
            email=email,
            username=username,
            full_name="Neythan Ayala Admin",
            password=make_password(password),  # ✅ FIX
            is_staff=True,
            is_superuser=True,
            is_active=True,  # ⚠️ recomendable
        )
        print(f"User {email} created successfully.")
    else:
        print(f"User {email} already exists.")

def remove_initial_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    email = "neythanayala670@gmail.com"
    User.objects.filter(email=email).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_alter_user_managers'),
    ]

    operations = [
        migrations.RunPython(create_initial_admin, reverse_code=remove_initial_admin),
    ]
    