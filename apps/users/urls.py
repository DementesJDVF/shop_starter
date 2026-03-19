from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .api.auth_views import LoginView, UserView
from .views import (
    AdminOnlyView,
    ChangeUserRoleView,
    CustomerOnlyView,
    MeView,
    RegisterView,
    VendorOnlyView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("admin/test/", AdminOnlyView.as_view(), name="admin_test"),
    path("vendor/test/", VendorOnlyView.as_view(), name="vendor_test"),
    path("customer/test/", CustomerOnlyView.as_view(), name="customer_test"),
    path("users/<int:user_id>/role/", ChangeUserRoleView.as_view(), name="change_user_role"),
    path("read/", UserView.as_view(), name="read"),
]
