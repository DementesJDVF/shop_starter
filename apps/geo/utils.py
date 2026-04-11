import math 

EARTH_RADIUS_KM = 6371.0088

def haversine(lat1, lon1, lat2, lon2):
    """Distancia en KM entre dos puntos (lat/lon en grados)."""
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c