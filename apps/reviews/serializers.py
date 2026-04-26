"""Serializers for product endpoints."""
from rest_framework import serializers
from apps.users.models import User
from apps.reviews.models import Review

class ReviewSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Review
        fields = "__all__"