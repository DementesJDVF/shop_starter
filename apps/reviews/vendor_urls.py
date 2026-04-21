from django.urls import path

from apps.reviews.views import VendorReviewView

urlpatterns = [
    path("", VendorReviewView.as_view(), name="vendor-review"),

]
