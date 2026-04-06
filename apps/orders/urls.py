from django.urls import path
from .views import CreateOrderView, VendorOrderListView

urlpatterns =[ 
    path('', CreateOrderView.as_view(), name='create-order'),
    path('vendor/', VendorOrderListView.as_view(), name='vendor-orders'),
]