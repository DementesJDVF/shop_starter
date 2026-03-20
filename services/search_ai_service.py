"""Service layer for AI-powered marketplace search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.ai_service import AIService, AIServiceError
from services.geo_service import GeoService
from services.product_service import ProductService


@dataclass(slots=True)
class SearchAIService:
    """Coordinates intent parsing + data retrieval from internal services."""

    ai_service: AIService

    def search(self, *, query: str, user_location: dict[str, float]) -> dict[str, Any]:
        filters = self._extract_filters(query=query)

        nearby_vendors = GeoService.get_nearby_vendors(
            lat=user_location["lat"],
            lng=user_location["lng"],
            distance_bucket=filters["distance"],
        )
        vendor_ids = list(nearby_vendors.keys())

        products = ProductService.search(
            category=filters["category"],
            price_range=filters["price_range"],
            vendor_ids=vendor_ids,
        )

        results = [
            {
                "product": product.name,
                "vendor": product.vendor.user.get_full_name() or product.vendor.user.email,
                "distance": nearby_vendors.get(str(product.vendor_id)),
                "price": float(product.price),
                "relevance": self._relevance_score(product_name=product.name, category=filters["category"]),
            }
            for product in products
        ]

        results.sort(key=lambda item: (item["distance"] if item["distance"] is not None else 9999, item["price"], -item["relevance"]))

        return {"filters": filters, "results": results}

    def _extract_filters(self, *, query: str) -> dict[str, str | None]:
        fallback = self._fallback_filters(query=query)

        try:
            ai_filters = self.ai_service.interpret_search_intent(query=query)
        except AIServiceError:
            return fallback

        return {
            "category": ai_filters.get("category") or fallback["category"],
            "price_range": self._normalize_price_range(ai_filters.get("price_range")) or fallback["price_range"],
            "distance": self._normalize_distance(ai_filters.get("distance")) or fallback["distance"],
        }

    @staticmethod
    def _normalize_price_range(raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        value = raw_value.lower().strip()
        return value if value in {"low", "medium", "high"} else None

    @staticmethod
    def _normalize_distance(raw_value: Any) -> str | None:
        if not isinstance(raw_value, str):
            return None
        value = raw_value.lower().strip()
        return value if value in {"near", "medium", "far"} else None

    @staticmethod
    def _fallback_filters(*, query: str) -> dict[str, str | None]:
        text = query.lower()

        category = None
        if "comida" in text or "hamburg" in text or "rápida" in text or "rapida" in text:
            category = "comida rápida"

        if "econ" in text or "barat" in text:
            price_range = "low"
        elif "premium" in text or "car" in text:
            price_range = "high"
        else:
            price_range = "medium"

        if "cerca" in text or "near" in text:
            distance = "near"
        elif "lejos" in text or "far" in text:
            distance = "far"
        else:
            distance = "medium"

        return {
            "category": category,
            "price_range": price_range,
            "distance": distance,
        }

    @staticmethod
    def _relevance_score(*, product_name: str, category: str | None) -> int:
        if category and category.lower() in product_name.lower():
            return 2
        return 1
