from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reviews.views import ReviewViewSet

router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='comment')
urlpatterns = [
    path('', include(router.urls)),
]