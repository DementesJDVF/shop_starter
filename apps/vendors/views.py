from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import VendorProfile
from .permissions import IsVendor
from .selectors import VendorSelectors
from .serializers import VendorPublicSerializer, VendorSerializer
from .services import VendorService


class VendorProfileCreateView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = VendorService.create_vendor_profile(
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(VendorSerializer(profile).data, status=status.HTTP_201_CREATED)


class VendorProfileDetailView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get_profile_or_404(self, user):
        profile = VendorSelectors.get_vendor_profile_by_user(user)
        if not profile:
            raise NotFound("Vendor profile not found")
        return profile

    def get(self, request):
        profile = self.get_profile_or_404(request.user)
        return Response(VendorSerializer(profile).data)

    def patch(self, request):
        profile = self.get_profile_or_404(request.user)

        serializer = VendorSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = VendorService.update_vendor_profile(
            request.user,
            profile,
            serializer.validated_data,
        )

        return Response(VendorSerializer(updated).data)


class VendorPublicView(generics.RetrieveAPIView):
    """Public vendor profile with dynamic rating metrics."""

    permission_classes = [AllowAny]
    serializer_class = VendorPublicSerializer
    lookup_field = "id"

    def get_queryset(self):
        return (
            VendorProfile.objects.with_rating()
            .select_related("user")
            .filter(status=VendorProfile.Status.ACTIVE)
        )


class VendorPublicDetailView(VendorPublicView):
    """Backward-compatible alias for existing imports."""