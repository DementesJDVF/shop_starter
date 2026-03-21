from django.urls import path

from apps.products.views.product_views import ProductCreateView, ProductDetailView, VendorProductListView

urlpatterns = [
    path('', ProductCreateView.as_view(), name='product-create'),
    path('my-products/', VendorProductListView.as_view(), name='vendor-products'),
    path('<int:product_id>/', ProductDetailView.as_view(), name='product-detail'),
]