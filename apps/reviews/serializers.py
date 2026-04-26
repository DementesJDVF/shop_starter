"""Serializers for product endpoints."""
from rest_framework import serializers
from apps.users.models import User
from apps.reviews.models import Review

class ReviewSerializer(serializers.ModelSerializer):
    client = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Review
        fields = ["id", "client", "rating", "review_text", "created_at", "product"]
        read_only_fields = ["user", "created_at"]

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        product = data.get('product')

        if not product:
            # Si estamos en un viewset anidado, el producto podría venir de los kwargs
            product_id = request.parser_context.get('kwargs', {}).get('product_id')
            from apps.products.models import Product
            product = Product.objects.get(id=product_id)

        # 1. ¿Es el usuario un comprador real?
        from apps.orders.models import Order
        has_purchased = Order.objects.filter(
            client=user,
            product=product,
            status=Order.Status.PAID
        ).exists()

        if not has_purchased:
            raise serializers.ValidationError("Solo puedes calificar productos que hayas comprado y pagado.")

        # 2. ¿Ya reseñó este producto?
        if Review.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("Ya has dejado una reseña para este producto.")

        return data