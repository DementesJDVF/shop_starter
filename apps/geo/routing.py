from django.urls import path
from .consumers import LocationConsumer

websocket_urlpatterns = [
    path("ws/location/", LocationConsumer.as_asgi()),
]