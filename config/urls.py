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

from apps.users.api.auth_views import LoginView
from apps.users.views import RegisterView, MeView
urlpatterns = [
    # admin
    path("admin/", admin.site.urls),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh_global"),

    # Apps
    path("api/users/", include("apps.users.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/orders/", include("apps.orders.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/geo/", include("apps.geo.urls")),
    path("api/reviews/", include("apps.reviews.urls")),
    path("api/chat/", include("apps.chat.urls")),
    path("api/auth/login/", LoginView.as_view(), name="login-alias"),
    path("api/auth/register/", RegisterView.as_view(), name="register-alias"),
    path("api/auth/me/", MeView.as_view(), name="me-alias"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh-alias"),
    
    # Alias para corregir llamadas antiguas del frontend a /api/vendors/
    path("api/vendors/", include("apps.reviews.urls")),


    # =========================================================================
    # 📚 PORTAL INTERACTIVO PARA PROGRAMADORES FRONTEND (DX)
    # =========================================================================
    # ¡No necesitas Postman! Entra a la ruta "localhost:8000/api/docs/" en tu
    # navegador para ver la interfaz interactiva. Podrás probar y enviar datos
    # vivos usando el botón "Try it out" en cada endpoint. Todos los endpoints
    # declarados en Django se auto-documentan aquí.
    
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Servir archivos media en desarrollo localmente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)