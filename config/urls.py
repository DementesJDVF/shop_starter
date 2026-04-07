from django.contrib import admin
from django.urls import path, include

# Swagger
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API principal (incluye products, categories, etc.)
    path("api/", include("apps.products.urls")),

    # 🔐 Auth JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 📦 Apps
    path("api/users/", include("apps.users.urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/audit/", include("apps.audit.urls")),

    # 📄 Documentación
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]