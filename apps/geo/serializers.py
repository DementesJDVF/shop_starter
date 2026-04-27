from rest_framework import serializers
from apps.geo.models import Location, LImages
from apps.users.models import User
from drf_extra_fields.fields import Base64ImageField
import cloudinary
import cloudinary.utils
import cloudinary.uploader
import os
class ImageSerializer(serializers.ModelSerializer):
    url_image = Base64ImageField()

    class Meta:
        model = LImages
        fields = ["id", "url_image", "is_main"]

    def to_representation(self, instance):
        """Asegura que la URL sea absoluta en producción sin romper el campo original."""
        ret = super().to_representation(instance)
        url = ret.get('url_image')
        
        # Si url_image es un string (TextField)
        if isinstance(url, str) and url.startswith(('http://', 'https://')):
            return ret

        if url and not url.startswith(('http', 'data:')):
            from django.conf import settings
            import os
            if os.environ.get('CLOUDINARY_URL') or not settings.DEBUG:
                public_id, _ = os.path.splitext(url.lstrip('/'))
                ret['url_image'] = cloudinary.utils.cloudinary_url(public_id, secure=True, format="jpg")[0]
            else:
                request = self.context.get("request")
                if request:
                    ret['url_image'] = request.build_absolute_uri(url)
        return ret
class LocationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    images = ImageSerializer(many=True, required=False)
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_status = serializers.CharField(source="user.status", read_only=True)
    products = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ["id", "user", "user_name", "user_email", "user_status", "latitude", "longitude", "description", "images", "products", "is_active"]

    def get_products(self, obj):
        """Devuelve un resumen de productos para la vista de Admin."""
        from apps.products.models import Product
        products = Product.objects.filter(vendor=obj.user).exclude(status='SOLD')[:4]
        data = []
        for p in products:
            img_url = None
            main_img = p.images.filter(is_main=True).first() or p.images.first()
            if main_img and main_img.url_image:
                url_str = str(main_img.url_image)
                if url_str.startswith(('http://', 'https://')):
                    img_url = url_str
                else:
                    try:
                        public_id, _ = os.path.splitext(url_str.lstrip('/'))
                        img_url = cloudinary.utils.cloudinary_url(public_id, secure=True, format="jpg", width=100, height=100, crop="fill")[0]
                    except: img_url = url_str
            
            data.append({
                "name": p.name,
                "price": p.price,
                "image": img_url,
                "status": p.status
            })
        return data

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
            "image",
            "is_active",
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
        if not main_image:
            main_image = obj.images.first()

        if main_image and main_image.url_image:
            url_str = str(main_image.url_image)
            if url_str.startswith(('http://', 'https://')):
                return url_str
            
            try:
                import os
                public_id, _ = os.path.splitext(url_str.lstrip('/'))
                import cloudinary.utils
                return cloudinary.utils.cloudinary_url(public_id, secure=True, format="jpg")[0]
            except Exception:
                return url_str

        return None