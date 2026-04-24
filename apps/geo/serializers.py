from rest_framework import serializers
from apps.geo.models import Location, LImages
from apps.users.models import User
from drf_extra_fields.fields import Base64ImageField
# from apps.users.constants import UserRoles
class ImageSerializer(serializers.ModelSerializer):
    url_image = Base64ImageField()

    class Meta:
        model = LImages
        fields = ["id", "url_image", "is_main"]

    def to_representation(self, instance):
        """Asegura que la URL sea absoluta en producción sin romper el campo original."""
        ret = super().to_representation(instance)
        url = ret.get('url_image')
        
        if url and not url.startswith(('http', 'data:')):
            from django.conf import settings
            if not settings.DEBUG:
                import cloudinary
                public_id = url.lstrip('/')
                ret['url_image'] = cloudinary.utils.cloudinary_url(public_id, secure=True)[0]
        return ret
class LocationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    images = ImageSerializer(many=True, required=False)
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    class Meta:
        model = Location
        fields = ["id", "user", "user_name", "user_email", "latitude", "longitude", "description", "images"]
    def validate_images(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Se permiten máximo 10 imágenes.")
        mains = [img for img in value if img.get("is_main")]
        if len(mains) > 1:
            raise serializers.ValidationError("Solo una imagen puede ser la principal.")
        return value

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        user = validated_data.pop("user", None) or self.context['request'].user
        
        # Usamos update_or_create porque un usuario solo puede tener UNA ubicación
        location, created = Location.objects.update_or_create(
            user=user,
            defaults=validated_data
        )
        
        # Si hay imágenes nuevas, limpiamos las anteriores y guardamos las nuevas
        if images_data:
            location.images.all().delete()
            for image_data in images_data:
                LImages.objects.create(location=location, **image_data)
            
        return location

    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", None)
        
        # Actualizamos la location
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si mandaron imágenes, las reemplazamos
        if images_data is not None:
            instance.images.all().delete() 
            for image_data in images_data:
                LImages.objects.create(location=instance, **image_data)
                
        return instance
    
class NearbyVendorSerializer(serializers.ModelSerializer):
    vendor = serializers.SerializerMethodField()
    distance = serializers.FloatField()
    image = serializers.SerializerMethodField()  # 🔥 NUEVO

    class Meta:
        model = Location
        fields = [
            "id",
            "latitude",
            "longitude",
            "description",
            "distance",
            "vendor",
            "image",  # 🔥 IMPORTANTE
        ]

    def get_vendor(self, obj):
        return {
            "id": obj.user.id,
            "name": getattr(obj.user, "username", None),
            "is_active": obj.user.is_active,
        }

    # 🔥 ESTA FUNCIÓN ES LA CLAVE
    def get_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()

        if main_image and main_image.url_image:
            url = main_image.url_image.url
            # Si ya es una URL absoluta (Cloudinary), la devolvemos tal cual
            if url.startswith(('http://', 'https://')):
                return url

            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(url)
            return url

        return None