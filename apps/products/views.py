"""API views for products CRUD."""
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from apps.products.models import Product, Category
from apps.products.serializers import (CreProSerializer,
                                       ReadProSerializer,
                                       CategorySerializer)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = CreProSerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # ¡Parche aquí!
        read_serializer = ReadProSerializer(serializer.instance, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
class ProductViewGet(viewsets.ModelViewSet):
    """
    Esta vista solo permite listar (GET /products/) 
    y ver detalle (GET /products/{id}/).
    """
    queryset = Product.objects.all() # O .filter(status='ACTIVE')
    serializer_class = ReadProSerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()
class CategoryViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Vista simple para ver la lista de categorías y el detalle de cada una.
    """
    queryset = Category.objects.all() # Solo mostramos las activas
    serializer_class = CategorySerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'