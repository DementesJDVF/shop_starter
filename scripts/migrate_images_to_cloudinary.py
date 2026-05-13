"""
Script para migrar imágenes locales existentes a Cloudinary.
Ejecutar con: python manage.py runscript migrate_images_to_cloudinary
  (o directamente: python scripts/migrate_images_to_cloudinary.py)
"""
import os
import sys
import django

# Setup Django si se ejecuta directamente
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
    django.setup()

import cloudinary.uploader
from apps.products.models import PImages
from django.conf import settings


def run():
    imgs = PImages.objects.filter(url_image__isnull=False)
    total = imgs.count()
    migrated = 0
    skipped = 0

    print(f"\n[*] Total de imagenes en DB: {total}\n")

    for img in imgs:
        raw_name = img.url_image.name
        local_path = os.path.join(settings.MEDIA_ROOT, raw_name)

        # Si ya es un public_id de Cloudinary (sin extensión o con sufijo), saltear
        if not os.path.exists(local_path):
            print(f"  [SKIP] archivo no existe localmente: {raw_name}")
            skipped += 1
            continue

        # Derivar el public_id quitando la extensión
        public_id = os.path.splitext(raw_name)[0]  # "products/images/uuid"

        print(f"  [UP] Subiendo '{raw_name}' -> public_id='{public_id}'")
        try:
            result = cloudinary.uploader.upload(
                local_path,
                public_id=public_id,
                overwrite=True,
                resource_type="image",
            )
            # Actualizar la DB con el public_id real devuelto por Cloudinary
            img.url_image.name = result["public_id"]
            img.save(update_fields=["url_image"])
            print(f"  [OK] {result['secure_url']}")
            migrated += 1
        except Exception as e:
            print(f"  [ERROR] {e}")

    print(f"\n[DONE] Migracion completa: {migrated} subidas, {skipped} saltadas de {total} total.\n")


if __name__ == "__main__":
    run()
