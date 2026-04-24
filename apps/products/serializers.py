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

    def to_internal_value(self, data):
        validated = super().to_internal_value(data)
        raw = validated.get('url_image', '')

        # Si llega como Base64 (data:image/jpeg;base64,...)
        if raw.startswith('data:'):
            try:
                header, encoded = raw.split(';base64,', 1)
                ext = header.split('/')[-1]
                file_data = base64.b64decode(encoded)
                filename = f"{uuid.uuid4()}.{ext}"
                validated['url_image'] = ContentFile(file_data, name=filename)
            except Exception:
                raise serializers.ValidationError({"url_image": "Imagen Base64 inválida."})
        
        # Si llega como URL externa
        elif raw.startswith(('http://', 'https://')):
            try:
                import requests
                from io import BytesIO
                response = requests.get(raw, timeout=10)
                response.raise_for_status()
                
                # Intentar obtener extensión del Content-Type
                content_type = response.headers.get('Content-Type', '')
                ext = 'jpg'
                if 'png' in content_type: ext = 'png'
                elif 'gif' in content_type: ext = 'gif'
                elif 'webp' in content_type: ext = 'webp'
                
                filename = f"{uuid.uuid4()}.{ext}"
                validated['url_image'] = ContentFile(response.content, name=filename)
            except Exception as e:
                raise serializers.ValidationError({"url_image": f"No se pudo descargar la imagen de la URL: {str(e)}"})

        return validated


class PImageReadSerializer(serializers.ModelSerializer):
    """Para leer imágenes — devuelve la URL completa."""
    url_image = serializers.SerializerMethodField()

    class Meta:
        model = PImages
        fields = ["id", "url_image", "is_main", "moderation_status"]

    def get_url_image(self, obj):
        if not obj.url_image:
            return None
        
        # IA DESACTIVADA: Mostramos todas las imágenes
        # if getattr(obj, 'moderation_status', None) == 'REJECTED':
        #     return None

        try:
            url = obj.url_image.url
            # Si ya es absoluta (Cloudinary), la devolvemos tal cual
            if url.startswith(('http://', 'https://')):
                return url

            from django.conf import settings
            # En producción Railway
            if not settings.DEBUG:
                import cloudinary
                public_id = url.lstrip('/')
                return cloudinary.utils.cloudinary_url(public_id, secure=True)[0]

            # En desarrollo local
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(url)
            return url
        except:
            return None


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
