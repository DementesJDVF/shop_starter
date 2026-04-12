from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet
from .views import nearby_vendors

router = DefaultRouter()
router.register(r"", LocationViewSet, basename="location")
urlpatterns = [
    # Las rutas estáticas DEBEN ir antes que el router genérico ("", include(router.urls))
    # de lo contrario el router piensa que "nearby" es un "ID" y lanza Error 404 Not Found.
    path("nearby/", nearby_vendors),
    path("vendors-locations/", LocationViewSet.as_view({'get': 'list'}), name="vendors-locations"),
    path("", include(router.urls)),
]