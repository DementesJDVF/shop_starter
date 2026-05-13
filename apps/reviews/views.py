from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.reviews.models import Review
from apps.reviews.serializers import (
    ReviewSerializer,
    ReviewInputSerializer,
    ReviewOutputSerializer,
    VendorReviewSummarySerializer,
)
from apps.reviews.services import submit_or_update_review, get_vendor_review_summary, update_review


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        import uuid
        # Soporta filtrar por vendedor vía URL (kwargs) o vía Query Param
        vendor_id = self.kwargs.get("vendor_id") or self.request.query_params.get("vendor")

        qs = Review.objects.all().order_by("-created_at")

        if vendor_id:
            try:
                uuid.UUID(str(vendor_id))
                qs = qs.filter(vendor__id=vendor_id)
            except (ValueError, TypeError):
                return Review.objects.none()

        return qs

    def list(self, request, *args, **kwargs):
        import uuid
        from django.db.models import Avg

        vendor_id = self.kwargs.get("vendor_id") or request.query_params.get("vendor")
        queryset = self.get_queryset()

        if vendor_id:
            try:
                uuid.UUID(str(vendor_id))
                avg_rating = queryset.aggregate(Avg("rate"))["rate__avg"] or 0
                total_reviews = queryset.count()
                serializer = self.get_serializer(queryset, many=True)
                return Response({
                    "average": round(float(avg_rating), 1),
                    "total": total_reviews,
                    "reviews": serializer.data,
                })
            except (ValueError, TypeError):
                return Response({"average": 0, "total": 0, "reviews": []})

        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        # Solo lectura es pública; escritura requiere autenticación.
        # Los administradores NO pueden colocar reseñas (neutralidad).
        if self.action in ["create", "update", "partial_update", "destroy"]:
            from apps.users.constants import UserRoles
            from rest_framework.exceptions import PermissionDenied

            if self.request.user.is_authenticated and self.request.user.role == UserRoles.ADMIN:
                raise PermissionDenied(
                    "Como Administrador debes mantener la neutralidad. No puedes publicar reseñas."
                )
            return [IsAuthenticated()]
        return [AllowAny()]

    def create(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            return super().create(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response(
                {"message": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def update(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            return super().update(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response(
                {"message": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def partial_update(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            return super().partial_update(request, *args, **kwargs)
        except DjangoValidationError as e:
            return Response(
                {"message": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        vendor_id = self.kwargs.get("vendor_id") or self.request.data.get("vendor")

        if not vendor_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"vendor": "Es necesario especificar el vendedor para la reseña."})

        # ANTI-FRAUDE: El usuario debe haber comprado a este vendedor
        from apps.orders.models import Order
        has_purchased = Order.objects.filter(
            client=self.request.user,
            vendor_id=vendor_id,
            status=Order.Status.PAID,
        ).exists()

        if not has_purchased:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Solo puedes reseñar a vendedores a los que les hayas comprado (y pagado)."
            )

        serializer.save(user=self.request.user, vendor_id=vendor_id)

    def perform_update(self, serializer):
        # SEGURIDAD: Solo el autor puede editar su reseña
        if serializer.instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para editar esta reseña.")
        serializer.save()

    def perform_destroy(self, instance):
        # SEGURIDAD: Solo el autor o un ADMIN pueden borrar
        user = self.request.user
        if instance.user != user and user.role != "ADMIN" and not user.is_superuser:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("No tienes permiso para eliminar esta reseña.")
        instance.delete()


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
        serializer = ReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = update_review(
            client=request.user,
            review_id=review_id,
            rating=serializer.validated_data["rating"],
            review_text=serializer.validated_data.get("review_text", ""),
        )
        return Response(ReviewOutputSerializer(review).data, status=status.HTTP_200_OK)