from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import NotFound

from .permissions import IsVendor
from .serializers import VendorSerializer
from .services import VendorService
from .selectors import VendorSelectors


class VendorProfileCreateView(APIView):

    permission_classes = [IsAuthenticated, IsVendor]

    def post(self, request):
        serializer = VendorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        profile = VendorService.create_vendor_profile(
            user=request.user,
            data=serializer.validated_data
        )

        return Response(
            VendorSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )


class VendorProfileDetailView(APIView):

    permission_classes = [IsAuthenticated, IsVendor]

    def patch(self, request):
        profile = VendorSelectors.get_vendor_profile_by_user(request.user)

        if not profile:
            raise NotFound("Vendor profile not found")

        serializer = VendorSerializer(
            profile,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        updated = VendorService.update_vendor_profile(
            request.user,
            profile,
            serializer.validated_data
        )

        return Response(VendorSerializer(updated).data)


class VendorPublicDetailView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, vendor_id):
        vendor = VendorSelectors.get_public_vendor_profile(vendor_id)

        serializer = VendorSerializer(vendor)
        return Response(serializer.data)