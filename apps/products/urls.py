from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views import (
    ProductViewSet,
    ProductCreateView,
    ProductCatalogView,
    ProductDetailPublicView,
    CategoryViewSet,
    CategoryViewGet,
    nearby_products,
)

# Creamos un ÚNICO router para toda la aplicación de productos
router = DefaultRouter()

# Registramos cada ViewSet con su propio prefijo
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    # Ruta para generación de descripción IA (vendedores)
    path("<int:pk>/generate_ai_description/", ProductViewSet.as_view({"post": "generate_ai_description"}), name="product-ai-gen"),
    path("suggest_description/", ProductViewSet.as_view({"post": "suggest_description"}), name="product-suggest-desc"),
    path("tasks/<str:task_id>/", ProductViewSet.as_view({"get": "get_task_status"}), name="product-task-status"),


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

    # Endpoint explícito de creación (solo POST)
    path("create/", ProductCreateView.as_view(), name="product-create"),

    # Rutas públicas específicas ANTES del router genérico
    path("catalog/", ProductCatalogView.as_view(), name="product-catalog-public"),
    path("nearby/", nearby_products, name="product-nearby"),
    path("<int:id>/", ProductDetailPublicView.as_view(), name="product-read-id"),

    # Resto de rutas del router (CRUD privado)
    path("", include(router.urls)),
]
