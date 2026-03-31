from django.db import transaction
from decimal import Decimal

from apps.orders.models import Order, OrderItem
from apps.products.models import Product


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order(client, items_data):

        if not items_data:
            raise ValueError("El pedido debe tener al menos un producto")

        product_ids = [item["product_id"] for item in items_data]

        products = Product.objects.select_related("vendor").filter(
            id__in=product_ids,
            status="ACTIVE"
        )

        if len(products) != len(items_data):
            raise ValueError("Uno o más productos no están disponibles")

        vendor = products.first().vendor

        if any(p.vendor != vendor for p in products):
            raise ValueError("Todos los productos deben pertenecer al mismo vendedor")

        order = Order.objects.create(
            client=client,
            vendor=vendor,
            total=0
        )

        total = Decimal("0.00")
        order_items = []

        for item in items_data:
            product = next(p for p in products if str(p.id) == str(item["product_id"]))

            if product.stock < item["quantity"]:
                raise ValueError(f"Stock insuficiente para {product.name}")

            subtotal = product.price * item["quantity"]
            total += subtotal

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=item["quantity"],
                    price_at_purchase=product.price
                )
            )

            product.stock -= item["quantity"]
            product.save()

        OrderItem.objects.bulk_create(order_items)

        order.total = total
        order.save()

        return order