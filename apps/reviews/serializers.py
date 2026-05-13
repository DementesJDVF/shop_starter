"""Serializers for review endpoints."""
from rest_framework import serializers
from apps.users.models import User
from apps.reviews.models import Review, VendorReview


class ReviewSerializer(serializers.ModelSerializer):
    client = serializers.ReadOnlyField(source="user.username")
    rating = serializers.DecimalField(source="rate", max_digits=2, decimal_places=1)
    review_text = serializers.CharField(source="content", allow_blank=True)

    class Meta:
        model = Review
        fields = ["id", "client", "rating", "review_text", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate(self, data):
        request = self.context.get("request")
        user = request.user if request else None
        # El vendedor ya se valida en el ViewSet (perform_create).
        # Añadir aquí validaciones extra si es necesario.
        return data


class ReviewInputSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review_text = serializers.CharField(required=False, allow_blank=True)


class ReviewOutputSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="client.username")

    class Meta:
        model = VendorReview
        fields = ["id", "client", "rating", "review_text", "created_at"]
        read_only_fields = ["id", "created_at"]


class VendorReviewSummarySerializer(serializers.Serializer):
    average = serializers.FloatField()
    total = serializers.IntegerField()
    reviews = ReviewOutputSerializer(many=True)