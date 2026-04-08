from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.users.permissions import IsVendor
from apps.products.models import Product, Category
from apps.products.serializers import (CreProSerializer,
                                       ReadProSerializer,
                                       CategorySerializer)

class ProductViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadProSerializer
        return CreProSerializer
    
    def get_queryset(self):
        """Filtra los productos para devolver solo los del vendedor autenticado."""
        user = self.request.user
        if user.is_authenticated:
            return Product.objects.filter(vendor=user)
        return Product.objects.none()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        # Asignamos al usuario actual si es vendedor
        if self.request.user.is_authenticated and self.request.user.role == 'VENDEDOR':
            serializer.save(vendor=self.request.user)
        else:
            serializer.save()

    def create(self, request, *args, **kwargs):
        # Usamos el serializador de creación pero respondemos con el de lectura
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Respondemos con el objeto completo para que el front se actualice bien
        read_serializer = ReadProSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
class ProductViewGet(viewsets.ModelViewSet):
    """
    Esta vista solo permite listar (GET /products/) 
    y ver detalle (GET /products/{id}/).
    """
    queryset = Product.objects.filter(status=Product.ProductStatus.ACTIVE)
    serializer_class = ReadProSerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'
    authentication_classes = []
    permission_classes = [AllowAny]

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
    # Usamos all_objects para saltar cualquier filtro de eliminación suave (soft-delete)
    queryset = Category.all_objects.all()
    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'