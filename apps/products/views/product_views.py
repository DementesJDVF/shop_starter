"""API views for products CRUD."""

from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product, Category
from apps.products.serializers.product_serializer import (ProductCreateSerializer,
                                                          ProductSerializer,
                                                          CreProSerializer,
                                                          CategorySerializer)
from apps.products.services.product_service import ProductService

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = CreProSerializer
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()
class CategoryViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Vista simple para ver la lista de categorías y el detalle de cada una.
    """
    queryset = Category.objects.filter(is_active=True) # Solo mostramos las activas
    serializer_class = CategorySerializer
class ProductCreateView(APIView):
    """Create products for active vendors."""
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor_profile = ProductService.validate_vendor_can_manage_products(user=request.user)
        product = ProductService.create_product(vendor_profile=vendor_profile, data=serializer.validated_data)
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
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated_product = ProductService.update_product(
            product_id=product_id,
            user=request.user,
            data=serializer.validated_data,
        )

        return Response(ProductSerializer(updated_product).data, status=status.HTTP_200_OK)

    def patch(self, request, product_id: int):
        serializer = ProductCreateSerializer(data=request.data, partial=True)
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
