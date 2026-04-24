import cloudinary
import cloudinary.uploader
from django.conf import settings

def upload_all_images():
    # Configurar Cloudinary manualmente
    import environ
    env = environ.Env()
    environ.Env.read_env()

    cloud_name = env("CLOUDINARY_CLOUD_NAME", default="")
    api_key = env("CLOUDINARY_API_KEY", default="")
    api_secret = env("CLOUDINARY_API_SECRET", default="")
    
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    print(f"Cloudinary configurado: cloud_name={cloud_name}")

    from apps.products.models import PImages
    import os
    from pathlib import Path

    all_images = PImages.objects.all()
    print(f"Total de imagenes en BD: {all_images.count()}")

    migrated = 0
    skipped = 0
    errors = 0

    media_root = settings.MEDIA_ROOT

    for img in all_images:
        name = img.url_image.name if img.url_image else None
        if not name:
            print(f"  ID={img.pk}: sin archivo, saltando.")
            skipped += 1
            continue

        # Buscar el archivo en disco
        if os.path.isabs(name):
            local_path = Path(name)
        else:
            local_path = Path(media_root) / name

        if not local_path.exists():
            print(f"  ID={img.pk}: ARCHIVO NO EXISTE en disco: {local_path}")
            errors += 1
            continue

        # Subir directamente a Cloudinary usando su SDK
        # public_id = como queremos que se llame en Cloudinary (sin extension)
        stem = local_path.stem  # nombre sin extension
        folder = "products/images"
        public_id = f"{folder}/{stem}"

        try:
            print(f"  Subiendo ID={img.pk}: {local_path.name} ...", end=' ')
            result = cloudinary.uploader.upload(
                str(local_path),
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            secure_url = result.get('secure_url', '')
            print(f"OK -> {secure_url[:80]}")

            # Actualizar la BD con el nombre que devuelve Cloudinary
            # El campo en la BD debe guardar el public_id
            img.url_image.name = result.get('public_id', public_id)
            img.save(update_fields=['url_image'])
            migrated += 1
        except Exception as e:
            print(f"ERROR ID={img.pk}: {e}")
            errors += 1

    print("=" * 40)
    print(f"Migradas: {migrated} | Saltadas: {skipped} | Errores: {errors}")
    print("=" * 40)

upload_all_images()
