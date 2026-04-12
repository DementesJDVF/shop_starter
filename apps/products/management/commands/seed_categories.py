from django.core.management.base import BaseCommand
from apps.products.models import Category


class Command(BaseCommand):
    help = 'Crea categorias predeterminadas para ShopStarter'

    def handle(self, *args, **options):
        categorias = [
            {'name': 'Electronica', 'description': 'Dispositivos, gadgets y accesorios tecnologicos', 'emoji': '', 'is_active': True},
            {'name': 'Ropa y Moda', 'description': 'Prendas de vestir, calzado y accesorios', 'emoji': '', 'is_active': True},
            {'name': 'Alimentos y Bebidas', 'description': 'Productos comestibles, snacks y bebidas artesanales', 'emoji': '', 'is_active': True},
            {'name': 'Hogar y Decoracion', 'description': 'Muebles, decoracion y articulos para el hogar', 'emoji': '', 'is_active': True},
            {'name': 'Deportes', 'description': 'Equipos deportivos, ropa y accesorios fitness', 'emoji': '', 'is_active': True},
            {'name': 'Arte y Manualidades', 'description': 'Obras de arte, artesanias y materiales creativos', 'emoji': '', 'is_active': True},
            {'name': 'Libros y Educacion', 'description': 'Libros, cursos y material educativo', 'emoji': '', 'is_active': True},
            {'name': 'Belleza y Cuidado', 'description': 'Cosmeticos, perfumes y productos de cuidado personal', 'emoji': '', 'is_active': True},
            {'name': 'Juguetes y Juegos', 'description': 'Juguetes, juegos de mesa y entretenimiento', 'emoji': '', 'is_active': True},
            {'name': 'Mascotas', 'description': 'Alimentos, accesorios y cuidado para mascotas', 'emoji': '', 'is_active': True},
        ]

        created = 0
        for cat in categorias:
            obj, was_created = Category.objects.get_or_create(
                name=cat['name'],
                defaults=cat
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Creada: {obj.name}'))
            else:
                self.stdout.write(f'  Ya existe: {obj.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nTotal categorias en BD: {Category.objects.count()} ({created} nuevas)'
        ))
