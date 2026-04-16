from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ValidationError

from apps.reviews.models import VendorReview
from apps.users.constants import UserRoles
from apps.users.models import User


def submit_or_update_review(client, vendor_id, rating, review_text=""):
    vendor = get_object_or_404(
        User,
        pk=vendor_id,
        role=UserRoles.VENDEDOR,
        status=User.Status.ACTIVE,
    )

    # REMOVED: Completed order validation requirement for review submission.

    review, created = VendorReview.objects.update_or_create(
        vendor=vendor,
        client=client,
        defaults={"rating": rating, "review_text": review_text},
    )
    review._created = created
    return review


def get_vendor_review_summary(vendor_id):
    vendor = get_object_or_404(User, pk=vendor_id, role=UserRoles.VENDEDOR)
    reviews = VendorReview.objects.filter(vendor=vendor).order_by("-created_at")
    aggregate = reviews.aggregate(avg_rating=Avg("rating"))
    average = aggregate["avg_rating"]
    average = round(float(average), 1) if average is not None else 0.0

    return {
        "average": average,
        "total": reviews.count(),
        "reviews": reviews,
    }
