from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.products.views.product_views import (ProductViewSet,
                                               ProductViewGet,
                                               CategoryViewSet,
                                               CategoryViewGet)
Create = DefaultRouter()
Create.register(r'', ProductViewSet)
Read = DefaultRouter()
# Registramos la ruta base para el listado general: /api/products/
Read.register(r'', ProductViewGet, basename='product-list')
CatCreate = DefaultRouter()
CatCreate.register(r'', CategoryViewSet)
CatRead = DefaultRouter()
# Registramos la ruta base para el listado general: /api/products/caregories/
CatRead.register(r'list', CategoryViewGet, basename='categories-list')
urlpatterns = [
    path('create/', include(Create.urls)),
    path('', include(Read.urls)),
    path('<int:id>/', ProductViewGet.as_view({'get': 'retrieve'}), name='product-read-id'),
    path('categories/create/', include(CatCreate.urls)),
    path('categories/', include(CatRead.urls)),
    path('categories/<int:id>/', CategoryViewGet.as_view({'get': 'retrieve'}), name='product-read-id'),
]