from apps.reviews.models import VendorReview


def get_reviews_for_vendor(vendor_id):
    return VendorReview.objects.filter(vendor_id=vendor_id).order_by("-created_at")
