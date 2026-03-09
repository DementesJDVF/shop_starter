from rest_framework import serializers
from .models import Vendor


class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = [
            "id",
            "status",
            "verified",
            "location_type",
            "reputation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "status",
            "verified",
            "reputation",
            "created_at",
            "updated_at",
        ]