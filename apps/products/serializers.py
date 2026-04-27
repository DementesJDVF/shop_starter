"""Serializers for product endpoints."""

from rest_framework import serializers
from apps.products.models import Category, Product, PImages
from django.db import transaction
import base64
import uuid
from django.core.files.base import ContentFile


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "emoji", "is_active"]


class PImageWriteSerializer(serializers.Serializer):
    """Acepta una imagen como string Base64 o URL."""
    url_image = serializers.CharField()  # Base64 string del frontend
    is_main = serializers.BooleanField(default=False)

    def validate(self, data):
        raw = data.get('url_image', '')

        # Si llega como Base64 (data:image/jpeg;base64,...)
        if raw.startswith('data:'):
            try:
                import cloudinary.uploader
                header, encoded = raw.split(';base64,', 1)
                file_data = base64.b64decode(encoded)
                
                # Subida directa a Cloudinary para evitar fallos de configuración de storage
                upload_result = cloudinary.uploader.upload(
                    file_data,
                    folder="products/images/",
                    resource_type="auto"
                )
                
                # Guardamos la URL COMPLETA para que sea infalible al leer
                data['url_image'] = upload_result['secure_url']
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error subiendo a Cloudinary: {e}")
                raise serializers.ValidationError({"url_image": f"Error al subir imagen a la nube: {str(e)}"})
        
        # Si llega como URL externa
        elif raw.startswith(('http://', 'https://')):
            try:
                import requests
                import cloudinary.uploader
                response = requests.get(raw, timeout=10)
                response.raise_for_status()
                
                upload_result = cloudinary.uploader.upload(
                    response.content,
                    folder="products/images/",
                    resource_type="auto"
                )
                # Guardamos la URL COMPLETA
                data['url_image'] = upload_result['secure_url']
            except Exception as e:
                raise serializers.ValidationError({"url_image": f"No se pudo procesar la imagen de la URL: {str(e)}"})

        return data


class PImageReadSerializer(serializers.ModelSerializer):
    """Para leer imágenes — devuelve la URL completa."""
    url_image = serializers.SerializerMethodField()

    class Meta:
        model = PImages
        fields = ["id", "url_image", "is_main", "moderation_status"]

    def get_url_image(self, obj):
        if not obj.url_image:
            return None

        # Si url_image es un string (TextField en el modelo)
        if isinstance(obj.url_image, str):
            if obj.url_image.startswith(('http://', 'https://')):
                return obj.url_image
            # Si es una ruta relativa, intentamos devolverla
            return obj.url_image

        try:
            # Fallback para cuando se usa ImageField real (aunque el modelo dice TextField)
            url = obj.url_image.url
            if url.startswith(('http://', 'https://')):
                return url
            return url
        except Exception:
            return str(obj.url_image) if obj.url_image else None


class CreProSerializer(serializers.ModelSerializer):
    """Serializer para CREAR/EDITAR productos (el vendedor envía datos)."""
    images = PImageWriteSerializer(many=True, required=False)
    vendor = serializers.PrimaryKeyRelatedField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'category', 'category_name',
            'name', 'description', 'ai_description', 'price', 'stock',
            'status', 'rejection_reason', 'is_featured', 'images'
        ]
        read_only_fields = ['vendor'] # 'status' is no longer read_only globally; we will handle permissions in the view.

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)
        for img_data in images_data:
            PImages.objects.create(product=product, **img_data)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if images_data is not None:
            # Opción: borrar imágenes anteriores o solo añadir
            # Por ahora solo añadimos las nuevas
            for img_data in images_data:
                PImages.objects.create(product=instance, **img_data)
        return instance


class ReadProSerializer(serializers.ModelSerializer):
    """Serializer para LEER productos (el cliente ve la lista/detalle)."""
    images = PImageReadSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.username', read_only=True)
    distance = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'vendor', 'vendor_name', 'category', 'category_name',
            'name', 'description', 'ai_description', 'price', 'stock',
            'status', 'rejection_reason', 'is_featured', 'images', 'created_at',
            'distance', 'latitude', 'longitude'
        ]

    def get_distance(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        
        user_lat = request.query_params.get('lat')
        user_lng = request.query_params.get('lng')

        if not (user_lat and user_lng):
            return None

        try:
            from apps.geo.models import Location
            from apps.geo.utils import haversine
            
            vendor_loc = Location.objects.filter(user=obj.vendor).first()
            if not vendor_loc:
                return None
                
            return round(haversine(
                user_lat, user_lng, 
                vendor_loc.latitude, vendor_loc.longitude
            ), 2)
        except Exception:
            return None

    def get_latitude(self, obj):
        try:
            from apps.geo.models import Location
            loc = Location.objects.filter(user=obj.vendor).first()
            return float(loc.latitude) if loc else None
        except: return None

    def get_longitude(self, obj):
        try:
            from apps.geo.models import Location
            loc = Location.objects.filter(user=obj.vendor).first()
            return float(loc.longitude) if loc else None
        except: return None


# Alias para compatibilidad con código existente
ProductSerializer = ReadProSerializer
