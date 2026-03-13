from django.contrib import admin
from django.urls import path, include

# JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Catalog
from apps.products.views.catalog_views import CatalogView

# Swagger / OpenAPI
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Autenticación JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Apps del sistema
    path("api/users/", include("apps.users.urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/audit/", include("apps.audit.urls")),

    # Catálogo público
    path("api/catalog/", CatalogView.as_view(), name="catalog-list"),

    # Documentación API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
