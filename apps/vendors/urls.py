from django.urls import path

from .views import VendorProfileCreateView, VendorProfileDetailView, VendorPublicView

urlpatterns = [
    path("", VendorProfileCreateView.as_view(), name="vendor-list"),
    path("me/", VendorProfileDetailView.as_view(), name="vendor-detail"),
    path("<uuid:id>/", VendorPublicView.as_view(), name="vendor-public-detail"),
]