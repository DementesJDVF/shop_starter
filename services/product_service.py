"""Cross-module product queries for AI search."""

from __future__ import annotations

from decimal import Decimal

from apps.products.models import Product
from apps.vendors.models import VendorProfile


class ProductService:
    """Read-oriented product service for discovery scenarios."""

    PRICE_RANGE_LIMITS = {
        "low": (None, Decimal("10000")),
        "medium": (Decimal("10000"), Decimal("30000")),
        "high": (Decimal("30000"), None),
    }

    @staticmethod
    def search(*, category: str | None, price_range: str, vendor_ids: list[str]):
        queryset = Product.objects.select_related("vendor", "vendor__user", "category").filter(
            status=Product.ProductStatus.ACTIVE,
            is_deleted=False,
            vendor__status=VendorProfile.Status.ACTIVE,
            vendor__user__is_active=True,
        )

        if vendor_ids:
            queryset = queryset.filter(vendor_id__in=vendor_ids)

        if category:
            queryset = queryset.filter(category__name__icontains=category)

        min_price, max_price = ProductService.PRICE_RANGE_LIMITS.get(price_range, (None, None))
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset
