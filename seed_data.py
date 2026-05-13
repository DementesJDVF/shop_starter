import os
import django
import random
from decimal import Decimal

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.users.models import User
from apps.users.constants import UserRoles
from apps.products.models import Category, Product
from apps.geo.models import Location
from django.db import transaction

# 1. Definir los datos maestros (Categorías y Vendedores temáticos)
VENDORS_DATA = [
    {
        "category": {"name": "Comida y Restaurantes", "emoji": "🍔", "desc": "Platos fuertes, comidas rápidas y postres."},
        "user": {
            "username": "food_vendor",
            "email": "food@shopstarter.com",
            "full_name": "El Rey de la Hamburguesa",
            "phone_number": "3001234567"
        },
        "location": {"lat": "2.441900", "lng": "-76.606200", "desc": "Restaurante Principal Centro"},
        "products": [
            {"name": "Hamburguesa Doble Carne", "desc": "Jugosa hamburguesa con doble carne Angus, queso cheddar y tocineta.", "price": "22000.00"},
            {"name": "Pizza Familiar Pepperoni", "desc": "Pizza en horno de leña, 10 porciones.", "price": "45000.00"},
            {"name": "Malteada de Vainilla", "desc": "Decorada con crema chantillí y cereza.", "price": "12000.00"},
        ]
    },
    {
        "category": {"name": "Ropa y Accesorios", "emoji": "👕", "desc": "Moda para hombre y mujer, zapatos y accesorios."},
        "user": {
            "username": "fashion_vendor",
            "email": "fashion@shopstarter.com",
            "full_name": "Moda Elegance",
            "phone_number": "3119876543"
        },
        "location": {"lat": "2.445200", "lng": "-76.612000", "desc": "Boutique en el norte"},
        "products": [
            {"name": "Chaqueta de Cuero", "desc": "Chaqueta de cuero sintético con forro interno.", "price": "120000.00"},
            {"name": "Zapatos Deportivos Runner", "desc": "Zapatos ultra-ligeros ideales para trotar.", "price": "180000.00"},
            {"name": "Gafas de Sol Polarizadas", "desc": "Estilo aviador con protección UV400.", "price": "45000.00"},
        ]
    },
    {
        "category": {"name": "Tecnología", "emoji": "💻", "desc": "Computadores, celulares y gadgets técnicos."},
        "user": {
            "username": "tech_vendor",
            "email": "tech@shopstarter.com",
            "full_name": "Tech Store Popayán",
            "phone_number": "3154567890"
        },
        "location": {"lat": "2.438500", "lng": "-76.602500", "desc": "Almacén de Tecnología Campanario"},
        "products": [
            {"name": "Laptop Gamer Pro", "desc": "Portátil de 15.6 pulgadas con tarjeta de video RTX 3060 y 16GB RAM.", "price": "4500000.00"},
            {"name": "Smartphone X12", "desc": "Teléfono de altísima gama, cámara 108MP, batería 5000mAh.", "price": "2300000.00"},
            {"name": "Auriculares Inalámbricos", "desc": "Audífonos Bluetooth con cancelación de ruido.", "price": "150000.00"},
            {"name": "Mouse Inalámbrico", "desc": "Mouse recargable ergonómico especial.", "price": "45000.00"},
        ]
    },
    {
        "category": {"name": "Hogar y Ferretería", "emoji": "🔧", "desc": "Todo lo necesario para construir o remodelar su hogar."},
        "user": {
            "username": "home_vendor",
            "email": "home@shopstarter.com",
            "full_name": "Ferretería El Maestro",
            "phone_number": "3201112233"
        },
        "location": {"lat": "2.450100", "lng": "-76.598000", "desc": "Bodega Principal al Oriente"},
        "products": [
            {"name": "Taladro Percutor 500W", "desc": "Ideal para trabajos livianos en el hogar, incluye brocas.", "price": "135000.00"},
            {"name": "Pintura Acrílica Blanca", "desc": "Galón de pintura lavable para interiores.", "price": "55000.00"},
            {"name": "Juego de Destornilladores", "desc": "Set de 15 piezas entre estría y pala magnetizados.", "price": "32000.00"},
        ]
    }
]

def run_seed():
    print("Iniciando el poblado de la base de datos...")

    with transaction.atomic():
        for item in VENDORS_DATA:
            # --- CATEGORIA ---
            cat_data = item["category"]
            category, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={
                    "emoji": cat_data["emoji"],
                    "description": cat_data["desc"],
                    "is_active": True
                }
            )
            if created:
                print(f"Categoria creada: {category.name}")

            # --- VENDEDOR ---
            user_data = item["user"]
            try:
                vendor = User.objects.get(email=user_data["email"])
                print(f"Vendedor {vendor.username} ya existia, saltando creacion.")
            except User.DoesNotExist:
                # El vendedor nace siendo ACTIVE para evitar fricciones en el frontend
                vendor = User.objects.create_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    password="Vendedor123!",
                    role=UserRoles.VENDOR,
                    status=User.Status.ACTIVE,
                    is_active=True,
                    full_name=user_data["full_name"],
                    phone_number=user_data["phone_number"],
                    document_type="NIT",
                    document_number=str(random.randint(10000000, 99999999))
                )
                print(f"Vendedor creado: {vendor.username}")

                # --- LOCALIZACIÓN GPS ---
                loc_data = item["location"]
                Location.objects.create(
                    user=vendor,
                    latitude=loc_data["lat"],
                    longitude=loc_data["lng"],
                    description=loc_data["desc"]
                )
                print(f"Ubicacion adjuntada al vendedor {vendor.username}")

            # --- PRODUCTOS ---
            for prod_data in item["products"]:
                obj, prod_created = Product.objects.get_or_create(
                    name=prod_data["name"],
                    vendor=vendor,
                    defaults={
                        "category": category,
                        "description": prod_data["desc"],
                        "price": Decimal(prod_data["price"]),
                        "stock": random.randint(10, 50),
                        "status": Product.ProductStatus.ACTIVE # ¡Producto ACTIVO!
                    }
                )
                if prod_created:
                    print(f"   Producto '{obj.name}' registrado a {vendor.username}")

    print("\nPOBLADO DE DATOS TERMINADO CON EXITO!")

if __name__ == "__main__":
    run_seed()
