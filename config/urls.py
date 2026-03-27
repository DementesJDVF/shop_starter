from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.products.views.catalog_views import CatalogView

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT (legacy/global)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Users API (kept in both prefixes to avoid breaking existing clients)
    path("api/", include("apps.users.urls")),
    path("api/users/", include("apps.users.urls")),

    # Domain APIs
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/catalog/", CatalogView.as_view(), name="catalog-list"),

    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
