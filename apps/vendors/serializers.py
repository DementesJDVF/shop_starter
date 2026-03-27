from rest_framework import serializers

from .models import VendorProfile


class VendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = VendorProfile
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


class VendorModerationSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=VendorProfile.Status.choices)
    verified = serializers.BooleanField()

    def validate(self, attrs):
        if attrs["verified"] and attrs["status"] != VendorProfile.Status.ACTIVE:
            raise serializers.ValidationError(
                {"verified": "Solo un vendedor ACTIVO puede quedar verificado."}
            )

        if attrs["status"] == VendorProfile.Status.BLOCKED and attrs["verified"]:
            raise serializers.ValidationError(
                {"status": "Un vendedor bloqueado no puede permanecer verificado."}
            )

        return attrs