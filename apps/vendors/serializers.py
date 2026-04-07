from decimal import Decimal, ROUND_HALF_UP

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


class VendorPublicSerializer(serializers.ModelSerializer):
    business_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vendor
        fields = ["id", "business_name", "average_rating", "total_reviews"]

    def get_business_name(self, obj) -> str:
        """Return vendor public business label."""
        return getattr(obj.user, "username", "")

    def get_average_rating(self, obj) -> float:
        """Return the annotated average rating rounded to 2 decimals."""
        average = getattr(obj, "average_rating", None)
        if average is None:
            return 0

        rounded = Decimal(str(average)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(rounded)