from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import (
    ProductViewSet,
    ProductViewGet,
    CategoryViewSet,
    CategoryViewGet,
)

router = DefaultRouter()
# Para VENDEDORES (Gestionar sus productos)
router.register(r"create", ProductViewSet, basename="product-admin")
# Para CLIENTES (Ver catálogo público)
router.register(r"catalog", ProductViewGet, basename="product-public")

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
]
