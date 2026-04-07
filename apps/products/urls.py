from django.urls import path, include
from .views import ProductViewSet, ProductViewGet, CategoryViewSet, CategoryViewGet
from rest_framework.routers import DefaultRouter


router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='products')
router.register(r'products-view', ProductViewGet, basename='products-view')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'categories-view', CategoryViewGet, basename='categories-view')

urlpatterns = router.urls


# Registramos la ruta base para el listado general: /api/products/caregories/
