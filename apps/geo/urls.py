from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet
from .views import nearby_vendors

router = DefaultRouter()
router.register(r"", LocationViewSet, basename="location")
urlpatterns = [
    path("", include(router.urls)),
    path("nearby/", nearby_vendors),
]