from django.contrib import admin
from django.urls import path, include
from apps.products.views.catalog_views import CatalogView

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

urlpatterns = [
    path('admin/', admin.site.urls),

    # API del proyecto
    path('api/', include('apps.users.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/vendors/', include('apps.vendors.urls')),
    path('api/catalog/', CatalogView.as_view(), name='catalog-list'),

    # OpenAPI Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    # Redoc (documentación alternativa)
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
]