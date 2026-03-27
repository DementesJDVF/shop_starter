from django.urls import path

from .views import (
    VendorModerationView,
    VendorProfileCreateView,
    VendorProfileDetailView,
    VendorPublicDetailView,
)

urlpatterns = [
    # Crear perfil de vendedor
    path("create/", VendorProfileCreateView.as_view(), name="vendor-create"),

    # Perfil del vendedor autenticado
    path("me/", VendorProfileDetailView.as_view(), name="vendor-me"),

    # Perfil público
    path("<uuid:vendor_id>/", VendorPublicDetailView.as_view(), name="vendor-public-detail"),

    # Moderación (admin)
    path("<uuid:vendor_id>/moderation/", VendorModerationView.as_view(), name="vendor-moderation"),
]