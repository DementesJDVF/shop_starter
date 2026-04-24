from django.db.models import QuerySet
from apps.products.models import Product
from apps.users.constants import UserRoles

class ProductService:
    """
    Service layer for Product-related business logic.
    Handles data retrieval and constraints.
    """

    @staticmethod
    def get_public_catalog(vendor_id: str = None) -> QuerySet[Product]:
        """
        Retrieves the public product catalog.
        Only shows ACTIVE products from ACTIVE vendors.
        Can be optionally filtered by a specific vendor.
        """
        queryset = Product.objects.filter(
            status=Product.ProductStatus.ACTIVE,
            vendor__status='ACTIVE',
            vendor__role=UserRoles.VENDEDOR
        ).order_by('-created_at')

        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        return queryset

    @staticmethod
    def get_public_product_detail(product_id: int) -> Product:
        """
        Retrieves a single public product detail if it is active.
        """
        return Product.objects.filter(
            id=product_id,
            status=Product.ProductStatus.ACTIVE,
            vendor__status='ACTIVE'
        ).first()

    @staticmethod
    def get_manageable_products(user) -> QuerySet[Product]:
        """
        Retrieves products that a specific user can manage in their dashboard.
        - Admins/Superusers see everything.
        - Vendors see their own products.
        - Others see nothing.
        """
        if not user.is_authenticated:
            return Product.objects.none()

        if user.role == UserRoles.ADMIN or user.is_superuser:
            return Product.objects.all().order_by('-created_at')
            
        if user.role == UserRoles.VENDEDOR:
            return Product.objects.filter(vendor=user).order_by('-created_at')

        return Product.objects.none()
