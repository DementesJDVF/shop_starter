"""Serializers for product endpoints."""
from rest_framework import serializers
from apps.users.models import User
from apps.reviews.models import Review

class ReviewSerializer(serializers.ModelSerializer):
    client = serializers.ReadOnlyField(source='user.username')
    rating = serializers.DecimalField(source='rate', max_digits=2, decimal_places=1)
    review_text = serializers.CharField(source='content', allow_blank=True)
    
    class Meta:
        model = Review
        fields = ["id", "client", "rating", "review_text", "created_at"]
        read_only_fields = ["user", "created_at"]

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        
        # El vendedor ya se valida en el ViewSet (perform_create)
        # Pero podemos añadir validaciones extra aquí si es necesario.
        return data