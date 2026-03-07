from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, MeView, AdminOnlyView, ChangeUserRoleView
from .api.auth_views import LoginView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('admin/test/', AdminOnlyView.as_view(), name='admin_test'),
    path('users/<int:user_id>/role/', ChangeUserRoleView.as_view(), name='change_user_role'),
]
