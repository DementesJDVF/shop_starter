from .models import Vendor


class VendorSelectors:

    @staticmethod
    def get_active_public_profiles():
        return Vendor.objects.filter(
            status=Vendor.Status.ACTIVE,
            is_deleted=False
        )

    @staticmethod
    def get_vendor_profile_by_user(user):
        return Vendor.objects.filter(user=user).first()