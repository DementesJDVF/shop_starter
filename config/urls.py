from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    # admin
    path("admin/", admin.site.urls),
  
    # API token
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_global"),

    # API del proyecto
    path('api/', include('apps.users.urls')),
    path("api/users/", include("apps.users.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path('api/geo/', include('apps.geo.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/reviews/', include('apps.reviews.urls')),
  
    # OpenAPI Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
  
    # Swagger UI
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui'),
  
    # Redoc (documentación alternativa)
    path('api/redoc/',SpectacularRedocView.as_view(url_name='schema'),name='redoc'),
    path("api/users/", include("apps.users.urls")),
]