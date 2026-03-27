"""API views for products CRUD."""

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.serializers.product_serializer import ProductCreateSerializer, ProductSerializer
from apps.products.services.product_service import ProductService


class ProductCreateView(APIView):
    """Create products for active vendors."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class VendorProductListView(APIView):
    """List products owned by authenticated vendor."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        vendor_profile = ProductService.validate_vendor_can_manage_products(user=request.user)
        products = ProductService.get_vendor_products(vendor_profile=vendor_profile)
        return Response(ProductSerializer(products, many=True).data, status=status.HTTP_200_OK)


class ProductDetailView(APIView):
    """Update or delete a single owned product."""

    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request, product_id: int):
        serializer = ProductCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        updated_product = ProductService.update_product(
            product_id=product_id,
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)

    def patch(self, request, product_id: int):
        serializer = ProductCreateSerializer(data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)

        updated_product = ProductService.update_product(
            product_id=product_id,
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)

    def delete(self, request, product_id: int):
        ProductService.delete_product(product_id=product_id, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)