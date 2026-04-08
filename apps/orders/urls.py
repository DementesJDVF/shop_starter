from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orders.views import OrdersViewSet

router = DefaultRouter()
router.register(r"", OrdersViewSet, basename="location")
urlpatterns = [
    path("", include(router.urls))
]