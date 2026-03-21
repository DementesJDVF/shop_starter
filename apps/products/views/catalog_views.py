"""Public catalog API views."""

from rest_framework import filters, permissions
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from apps.products.serializers.catalog_serializer import PublicProductSerializer
from apps.products.services.product_service import ProductService


class CatalogPagination(PageNumberPagination):
    """Pagination for catalog endpoint."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CatalogView(ListAPIView):
    """Public catalog list with search, ordering and pagination."""

    permission_classes = (permissions.AllowAny,)
    serializer_class = PublicProductSerializer
    pagination_class = CatalogPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("price", "created_at", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        return ProductService.get_public_catalog()
