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

        quantities_by_product = {}
        for item in items_data:
            quantity = item["quantity"]
            if quantity <= 0:
                raise ValueError("La cantidad debe ser mayor que cero")
            product_id = str(item["product_id"])
            quantities_by_product[product_id] = quantities_by_product.get(product_id, 0) + quantity
            
        product_ids = list(quantities_by_product.keys())
        
        products = Product.objects.select_for_update().select_related("vendor").filter(
            id__in=product_ids,
            status="ACTIVE"
        )

        if products.count() != len(product_ids):
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
        products_by_id = {str(product.id): product for product in products}

        for product_id, quantity in quantities_by_product.items():
            product = products_by_id[product_id]

            if product.stock < quantity:
                raise ValueError(f"Stock insuficiente para {product.name}")

            subtotal = product.price * quantity
            total += subtotal

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_at_purchase=product.price
                )
            )

            product.stock -= quantity
            product.save(update_fields=["stock", "updated_at"])

        OrderItem.objects.bulk_create(order_items)

        order.total = total
        order.save()

        return order