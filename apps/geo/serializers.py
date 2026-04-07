from rest_framework import serializers
from apps.geo.models import Location
from apps.users.models import User
from apps.users.constants import UserRoles
from .models import VendorProfile
class LocationSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.VENDOR))
    class Meta:
        model = Location
        fields = "__all__"
    def create(self, validated_data):
        location = Location.objects.create(**validated_data) 
        return location
    
    def valid_latitude(self,value):
        if value < -90 or value > 90:
            raise serializers.ValidationError(
                "la latitude debe estar entre -90 y 90"
            )
        return value
        
class VendorLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = VendorProfile
        fields = ["latitude", "longitude"]

    def validate(self, data):
        user = self.context["request"].user

        # 🔐 SOLO vendedor activo
        if not hasattr(user, "vendorprofile"):
            raise serializers.ValidationError("No eres vendedor")

        if not user.vendorprofile.is_active:
            raise serializers.ValidationError("Vendedor inactivo")

        lat = data.get("latitude")
        lng = data.get("longitude")

        # 🌍 Validación coordenadas
        if not (-90 <= lat <= 90):
            raise serializers.ValidationError("Latitud inválida")

        if not (-180 <= lng <= 180):
            raise serializers.ValidationError("Longitud inválida")

        return data