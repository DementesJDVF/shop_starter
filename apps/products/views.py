"""API views for products CRUD."""
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from apps.products.models import Category, Product, PComments
from apps.products.serializers import (CategorySerializer,
                                       ProductSerializer,
                                       PCommentSerializer)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        serializer.save()
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    # Si necesitas lógica extra al añadir (ej. asignar el usuario actual),
    # puedes sobrescribir esta función:
    def perform_create(self, serializer):
        # Aquí podrías, por ejemplo, validar algo antes de guardar
        serializer.save()
class CommentViewSet(viewsets.ModelViewSet):
    queryset = PComments.objects.all()
    serializer_class = PCommentSerializer
    permission_classes = [AllowAny]
    def perform_create(self, serializer):
        serializer.save()