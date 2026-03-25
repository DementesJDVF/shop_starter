from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsAdmin
from .permissions import IsVendor
from .selectors import VendorSelectors

from .serializers import VendorModerationSerializer, VendorSerializer

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

class VendorModerationView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, vendor_id):
        profile = VendorSelectors.get_vendor_profile_by_id(vendor_id)
        serializer = VendorModerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = VendorService.update_vendor_moderation(
            admin_user=request.user,
            profile=profile,
            status=serializer.validated_data["status"],
            verified=serializer.validated_data["verified"],
        )

        return Response(VendorSerializer(updated).data)

class VendorPublicDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, vendor_id):
        vendor = VendorSelectors.get_public_vendor_profile(vendor_id)
        serializer = VendorSerializer(vendor)
        return Response(serializer.data)
