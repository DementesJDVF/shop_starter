from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema

from apps.reviews.models import Review
from apps.reviews.serializers import (
    ReviewSerializer,
    ReviewInputSerializer,
    ReviewOutputSerializer,
    VendorReviewSummarySerializer,
)
from apps.reviews.services import submit_or_update_review, get_vendor_review_summary


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save()


class VendorReviewView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    @extend_schema(
        request=ReviewInputSerializer,
        responses={201: ReviewOutputSerializer, 200: ReviewOutputSerializer},
    )
    def post(self, request, vendor_id):
        serializer = ReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = submit_or_update_review(
            request.user,
            vendor_id,
            serializer.validated_data["rating"],
            serializer.validated_data.get("review_text", ""),
        )
        status_code = status.HTTP_201_CREATED if getattr(review, "_created", False) else status.HTTP_200_OK
        return Response(ReviewOutputSerializer(review).data, status=status_code)

    def get(self, request, vendor_id):
        summary = get_vendor_review_summary(vendor_id)
        return Response(VendorReviewSummarySerializer(summary).data)


class VendorReviewEditView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(request=ReviewInputSerializer, responses={200: ReviewOutputSerializer})
    def patch(self, request, review_id):
        from apps.reviews.services import update_review
        serializer = ReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = update_review(
            client=request.user,
            review_id=review_id,
            rating=serializer.validated_data["rating"],
            review_text=serializer.validated_data.get("review_text", ""),
        )
        return Response(ReviewOutputSerializer(review).data, status=status.HTTP_200_OK)