from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reviews.views import ReviewViewSet

router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='comment')

urlpatterns = [
    # Ruta específica para reviews de un vendedor: GET /api/vendors/{vendor_id}/reviews/
    path('<uuid:vendor_id>/reviews/', ReviewViewSet.as_view({'get': 'list'}), name='vendor-reviews'),
    # Compatibilidad con versión anterior del frontend
    path('vendors/<uuid:vendor_id>/reviews/', ReviewViewSet.as_view({'get': 'list'}), name='vendor-reviews-legacy'),
    path('', include(router.urls)),
]