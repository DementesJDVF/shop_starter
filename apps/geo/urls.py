from django.urls import path
from .views import vendors_locations, location_detail

urlpatterns = [
    path('vendors-locations/', vendors_locations),
    path('vendors-locations/<uuid:id>', location_detail),
]