from rest_framework import serializers
from apps.geo.models import Location, LImages
from apps.users.models import User
from drf_extra_fields.fields import Base64ImageField
# from apps.users.constants import UserRoles
class ImageSerializer(serializers.ModelSerializer):
    url_image = Base64ImageField () # Allows you to receive a string in base64 and save it as a file
    class Meta:
        model = LImages
        fields = ["id", "url_image", "is_main"]
class LocationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    images = ImageSerializer(many=True, required=False)
    class Meta:
        model = Location
        fields = "__all__"
    def validate_images(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Se permiten máximo 10 imágenes.")
        mains = [img for img in value if img.get("is_main")]
        if len(mains) > 1:
            raise serializers.ValidationError("Solo una imagen puede ser la principal.")
        return value

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        location = Location.objects.create(**validated_data)
        
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