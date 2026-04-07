from decimal import Decimal

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.users.constants import UserRoles
from apps.vendors.models import VendorProfile


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(source="product.id", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product_id", "product_name", "quantity", "price", "subtotal")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    customer_id = serializers.UUIDField(source="customer.id", read_only=True)
    vendor_id = serializers.UUIDField(source="vendor.id", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "customer_id",
            "vendor_id",
            "status",
            "total",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentication credentials were not provided")
        if user.role != UserRoles.CUSTOMER:
            raise PermissionDenied("Solo clientes pueden crear pedidos")

        raw_items = attrs.get("items") or []
        product_ids = [item["product_id"] for item in raw_items]

        if len(set(product_ids)) != len(product_ids):
            raise serializers.ValidationError("No se permiten productos repetidos en el pedido")

        products = {
            product.id: product
            for product in Product.objects.select_related("vendor").filter(id__in=product_ids)
        }

        if len(products) != len(product_ids):
            raise serializers.ValidationError("Uno o más productos no existen")

        vendor_id = None
        validated_items = []

        for item in raw_items:
            product = products[item["product_id"]]
            if product.status != Product.ProductStatus.ACTIVE:
                raise serializers.ValidationError(
                    f"El producto '{product.name}' no está activo"
                )

            if product.vendor.status != VendorProfile.Status.ACTIVE:
                raise serializers.ValidationError(
                    f"El vendedor del producto '{product.name}' está bloqueado o inactivo"
                )

            if vendor_id and vendor_id != product.vendor_id:
                raise serializers.ValidationError(
                    "Todos los productos deben pertenecer al mismo vendedor"
                )
            vendor_id = product.vendor_id

            if item["quantity"] > product.stock:
                raise serializers.ValidationError(
                    f"Stock insuficiente para '{product.name}'"
                )

            validated_items.append(
                {
                    "product": product,
                    "quantity": item["quantity"],
                    "price": product.price,
                    "subtotal": product.price * Decimal(item["quantity"]),
                }
            )

        attrs["validated_items"] = validated_items
        attrs["vendor"] = validated_items[0]["product"].vendor
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        validated_items = validated_data["validated_items"]

        order = Order.objects.create(
            customer=request.user,
            vendor=validated_data["vendor"],
            status=Order.Status.CREATED,
            total=Decimal("0.00"),
        )

        order_items = []
        total = Decimal("0.00")

        for item in validated_items:
            total += item["subtotal"]
            order_items.append(
                OrderItem(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                    price=item["price"],
                    subtotal=item["subtotal"],
                )
            )

        OrderItem.objects.bulk_create(order_items)
        order.total = total
        order.save(update_fields=["total", "updated_at"])

        return order

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data