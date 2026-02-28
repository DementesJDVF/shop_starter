from django.urls import path
from .views import RegisterView, LoginView, MeView, AdminOnlyView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('admin/test/', AdminOnlyView.as_view(), name='admin_test'),
]
