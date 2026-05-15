from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter
from apps.users.views import AdminUserViewSet

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

from .api.auth_views import LoginView, UserView, LogoutView, CustomTokenRefreshView, UserViewForUsers
from .api.password_reset_views import RequestPasswordResetView, ConfirmPasswordResetView
from .views import (
    AdminOnlyView,
    ChangeUserRoleView,
    ChangeUserStatusView,
    CustomerOnlyView,
    MeView,
    RegisterView,
    VendorOnlyView,
    MyProfileView,
    MyProfilePictureView,
)

urlpatterns = [
    path('', include(router.urls)),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/password-reset/", RequestPasswordResetView.as_view(), name="password_reset_request"),
    path("auth/password-reset-confirm/", ConfirmPasswordResetView.as_view(), name="password_reset_confirm"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("admin/test/", AdminOnlyView.as_view(), name="admin_test"),
    path("vendor/test/", VendorOnlyView.as_view(), name="vendor_test"),
    path("customer/test/", CustomerOnlyView.as_view(), name="customer_test"),

    # 🆕 Mi perfil y foto de perfil
    path("me/profile/", MyProfileView.as_view(), name="my_profile"),
    path("me/profile-picture/", MyProfilePictureView.as_view(), name="my_profile_picture"),

    path("list/", UserView.as_view(), name="read"),
    path("listusers/", UserViewForUsers.as_view(), name="read"),

    path("<str:pk>/", AdminUserViewSet.as_view({'delete': 'destroy'}), name="user-delete"),

    path("<str:user_id>/role/", ChangeUserRoleView.as_view(), name="change_user_role"),
    path("<str:user_id>/status/", ChangeUserStatusView.as_view(), name="change_user_status"),
]