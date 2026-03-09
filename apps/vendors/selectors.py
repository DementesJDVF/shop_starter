from .models import VendorProfile


class VendorSelectors:

    @staticmethod
    def get_active_public_profiles():
        return VendorProfile.objects.filter(
            status=VendorProfile.Status.ACTIVE,
            is_deleted=False
        )

    @staticmethod
    def get_vendor_profile_by_user(user):
        return VendorProfile.objects.filter(user=user).first()