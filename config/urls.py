from django.contrib import admin
from django.urls import path, include
from apps.products.views.catalog_views import CatalogView
from apps.products.views.category_views import CategoryListCreateView, CategoryDetailView

# Swagger
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.products.views.catalog_views import CatalogView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_global"),

    path("api/users/", include("apps.users.urls")),
    path("api/vendors/", include("apps.vendors.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/catalog/", CatalogView.as_view(), name="catalog-list"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui'),
]
