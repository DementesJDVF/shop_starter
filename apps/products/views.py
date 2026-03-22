"""API views for products CRUD."""
from rest_framework import viewsets
from apps.products.models import Product, Category
from apps.products.serializers import (CreProSerializer,
                                       ReadProSerializer,
                                       CategorySerializer)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = CreProSerializer
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()
class ProductViewGet(viewsets.ModelViewSet):
    """
    Esta vista solo permite listar (GET /products/) 
    y ver detalle (GET /products/{id}/).
    """
    queryset = Product.objects.filter(status='ACTIVE') # O .all()
    serializer_class = ReadProSerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'
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
    queryset = Category.objects.all() # Solo mostramos las activas
    serializer_class = CategorySerializer
    # Especificamos que busque por el campo 'id'
    lookup_field = 'id'