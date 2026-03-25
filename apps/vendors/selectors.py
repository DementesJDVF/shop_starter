from django.shortcuts import get_object_or_404

from .models import Vendor


class VendorSelectors:

    @staticmethod
    def get_vendor_profile_by_user(user):
        return Vendor.objects.filter(user=user).first()

    @staticmethod
    def get_vendor_profile_by_id(vendor_id):
        return get_object_or_404(Vendor, id=vendor_id, is_deleted=False)


    @staticmethod
    def get_public_vendor_profile(vendor_id):
        return get_object_or_404(
            Vendor,
            id=vendor_id,
            status=Vendor.Status.ACTIVE,
            verified=True,
            is_deleted=False,
        )