from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import (
    ProductViewSet,
    ProductViewGet,
    CategoryViewSet,
    CategoryViewGet,
    nearby_products,
)

# Creamos un ÚNICO router para toda la aplicación de productos
router = DefaultRouter()

# Registramos cada ViewSet con su propio prefijo
router.register(r'products', ProductViewSet, basename='product')
router.register(r'create', ProductViewSet, basename='product-create')  # Alias usado por el frontend
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    # Ruta pública de categorías (para vendedores y clientes)
    path("get-categories/", CategoryViewGet.as_view({'get': 'list'}), name="category-list-public"),

    # Rutas administrativas de categorías (CRUD completo)
    path("categories/admin/", CategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name="category-admin-list"),
    path("categories/admin/<int:pk>/", CategoryViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name="category-admin-detail"),

    # Resto de rutas del router
    path("", include(router.urls)),
    path("<int:id>/", ProductViewGet.as_view({"get": "retrieve"}), name="product-read-id"),

    # Ruta pública para el catálogo de clientes (solo productos ACTIVE)
    path("catalog/", ProductViewGet.as_view({"get": "list"}), name="product-catalog-public"),
    path("nearby/", nearby_products, name="product-nearby"),
]
