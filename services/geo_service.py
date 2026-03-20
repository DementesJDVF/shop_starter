"""Geolocation domain services."""

from __future__ import annotations

import math

from apps.geo.models import Location
from apps.vendors.models import VendorProfile


class GeoService:
    """Resolve nearby vendors using last known location."""

    DISTANCE_KM_BY_BUCKET = {
        "near": 3.0,
        "medium": 8.0,
        "far": 20.0,
    }

    @staticmethod
    def get_nearby_vendors(*, lat: float, lng: float, distance_bucket: str) -> dict[str, float]:
        max_distance_km = GeoService.DISTANCE_KM_BY_BUCKET.get(distance_bucket, 8.0)

        locations = (
            Location.objects.select_related("vendor", "vendor__user")
            .filter(vendor__status=VendorProfile.Status.ACTIVE, vendor__user__is_active=True)
            .order_by("vendor_id", "-timestamp")
        )

        nearest_by_vendor: dict[str, float] = {}
        for location in locations:
            vendor_key = str(location.vendor_id)
            if vendor_key in nearest_by_vendor:
                continue

            distance = GeoService._haversine_km(lat, lng, location.latitude, location.longitude)
            if distance <= max_distance_km:
                nearest_by_vendor[vendor_key] = round(distance, 2)

        return nearest_by_vendor

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radius_km = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        return 2 * radius_km * math.asin(math.sqrt(a))
