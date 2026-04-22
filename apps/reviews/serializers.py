"""Serializers for review endpoints."""
from rest_framework import serializers
from apps.orders.models import Order
from apps.users.models import User
from apps.reviews.models import Review, VendorReview

class ReviewSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Review
        fields = "__all__"


class ReviewInputSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    review_text = serializers.CharField(required=False, allow_blank=True)


class ReviewOutputSerializer(serializers.ModelSerializer):
    client = serializers.CharField(source="client.username")

    class Meta:
        model = VendorReview
        fields = [ "id", "client", "rating", "review_text", "created_at"]
        read_only_fields = ["id", "created_at"]

class VendorReviewSummarySerializer(serializers.Serializer):
    average = serializers.FloatField()
    total = serializers.IntegerField()
    reviews = ReviewOutputSerializer(many=True)
