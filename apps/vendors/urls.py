from django.urls import path
from .views import VendorProfileCreateView, VendorProfileDetailView

urlpatterns = [
    path("", VendorProfileCreateView.as_view(), name="vendor-list"),
    path("me/", VendorProfileDetailView.as_view(), name="vendor-detail"),
]