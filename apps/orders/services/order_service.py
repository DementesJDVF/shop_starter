from decimal import Decimal

from django.db import transaction

from apps.orders.models import Order, OrderItem


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(customer, vendor, validated_items):
        order = Order.objects.create(
            customer=customer,
            vendor=vendor,
            status=Order.Status.CREATED,
            total=Decimal("0.00"),
        )

        total = Decimal("0.00")
        order_items = []

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