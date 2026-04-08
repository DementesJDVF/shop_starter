from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import (ProductViewSet,
                                 CategoryViewSet)
# Creamos un ÚNICO router para toda la aplicación de productos
router = DefaultRouter()
# Registramos cada ViewSet con su propio prefijo
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
urlpatterns = [
    # Esto generará: /products/, /categories/, /comments/ y sus respectivos CRUDs
    path('', include(router.urls)),
]
