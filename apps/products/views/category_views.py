"""API views for category listing and creation."""

from rest_framework import permissions
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView

from apps.products.models import Category
from apps.products.serializers.category_serializer import CategorySerializer


class CategoryListCreateView(ListCreateAPIView):
    """Allow listing and creating categories."""

    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Category.objects.filter(is_deleted=False).order_by("name")


class CategoryDetailView(RetrieveAPIView):
    """Return a category by id."""

    serializer_class = CategorySerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Category.objects.filter(is_deleted=False)
    lookup_url_kwarg = "category_id"