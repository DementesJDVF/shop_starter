from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views.product_views import (ProductCreateView,
                                               ProductDetailView,
                                               VendorProductListView,
                                               ProductViewSet,
                                               CategoryViewSet,
                                               CategoryViewGet)

Create = DefaultRouter()
Create.register(r'', ProductViewSet)
CatCreate = DefaultRouter()
CatCreate.register(r'create', CategoryViewSet)

urlpatterns = [
    path('create-old/', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
    path('create/', include(Create.urls)),
    path('categories/', include(CatCreate.urls)),
    path('categories/read/', CategoryViewGet.as_view({'get': 'list'}), name='categorie-read'),
]