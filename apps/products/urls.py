from django.urls import path

from apps.products.views.category_views import CategoryDetailView, CategoryListCreateView
from apps.products.views.product_views import ProductCreateView, ProductDetailView, VendorProductListView

urlpatterns = [
    path('', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),

    path('categories/', CategoryListCreateView.as_view(), name='categories-list'),
    path('categories', CategoryListCreateView.as_view(), name='categories-list-no-slash'),
    path('categories/<int:category_id>/', CategoryDetailView.as_view(), name='category-detail'),
]