"""Serializers for product endpoints."""
from rest_framework import serializers
from apps.orders.models import Order
from apps.users.models import User
from apps.reviews.models import Review

class ReviewSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = Review
        fields = "__all__"