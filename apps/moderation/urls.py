from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RejectedImageViewSet

router = DefaultRouter()
router.register(r'rejected-images', RejectedImageViewSet, basename='rejected-image')

urlpatterns = [
    path('', include(router.urls)),
]