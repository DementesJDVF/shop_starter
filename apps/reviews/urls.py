from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.reviews.views import ReviewViewSet, VendorReviewEditView


router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='comment')
urlpatterns = [
    path('', include(router.urls)),
    path("edit/<uuid:review_id>/", VendorReviewEditView.as_view()),
]

