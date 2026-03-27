from rest_framework.routers import DefaultRouter
from .auth_views import UserViewSet

router_user = DefaultRouter()
router_user.register(
    prefix='users' , viewset= UserViewSet, basename='users'
)