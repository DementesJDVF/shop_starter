from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views.product_views import (ProductCreateView,
                                               ProductDetailView,
                                               VendorProductListView,
                                               ProductViewSet,
                                               ProductViewGet,
                                               CategoryViewSet,
                                               CategoryViewGet)

Create = DefaultRouter()
Create.register(r'', ProductViewSet)
Read = DefaultRouter()
# Registramos la ruta base para el listado general: /api/products/
Read.register(r'', ProductViewGet, basename='product-list')
CatCreate = DefaultRouter()
CatCreate.register(r'create', CategoryViewSet)

urlpatterns = [
    path('create-old/', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('create/', include(Create.urls)),
    path('', include(Read.urls)),
    path('products/<int:id>/', ProductViewGet.as_view({'get': 'retrieve'}), name='product-read-id'),
    path('categories/', include(CatCreate.urls)),
    path('categories/read/', CategoryViewGet.as_view({'get': 'list'}), name='categorie-read'),
]