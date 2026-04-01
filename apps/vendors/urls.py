from django.urls import path
from .views import (
    VendorProfileCreateView,
    VendorProfileDetailView,
    VendorPublicDetailView
)

urlpatterns = [
    path("", VendorProfileCreateView.as_view(), name="vendor-list"),
    path("me/", VendorProfileDetailView.as_view(), name="vendor-detail"),
    path("<int:vendor_id>/", VendorPublicDetailView.as_view(), name="vendor-public-detail"),
]