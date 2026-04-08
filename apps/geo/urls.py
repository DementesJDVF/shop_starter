from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import vendors_locations, location_detail, LocationViewSet
from .views import update_vendor_location

Create = DefaultRouter()
Create.register(r"", LocationViewSet)
Read = DefaultRouter()
Read.register(r"", LocationViewSet, basename="location-list")
urlpatterns = [
    path("create/", include(Create.urls)),
    path("", include(Read.urls)),
    path('vendors-locations/', vendors_locations),
    path('vendors-locations/<uuid:pk>/', location_detail),
    path('vendor/update-location/', update_vendor_location),
]