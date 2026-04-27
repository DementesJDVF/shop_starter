from django.db.models.query import QuerySet
from apps.products.models import Product
from apps.users.constants import UserRoles
import uuid

class ProductService:
    """
    Service layer for Product-related business logic.
    Handles data retrieval and constraints.
    """

    @staticmethod
    def get_public_catalog(vendor_id: str = None) -> QuerySet[Product]:
        """
        Retrieves the public product catalog.
        Only shows AVAILABLE products with stock > 0 from ACTIVE vendors.
        """
        queryset = Product.objects.filter(
            status=Product.ProductStatus.AVAILABLE,
            stock__gt=0,
            vendor__status='ACTIVE',
            vendor__role=UserRoles.VENDEDOR,
            vendor__locations__is_active=True
        ).order_by('-created_at')

        if vendor_id:
            try:
                # Validar que sea un UUID válido para evitar el Error 500 de Django
                uuid.UUID(str(vendor_id))
                queryset = queryset.filter(vendor_id=vendor_id)
            except (ValueError, TypeError):
                return Product.objects.none()

        return queryset

    @staticmethod
    def get_public_product_detail(product_id: str) -> Product:
        """
        Retrieves a single public product detail if it is available.
        """
        try:
            uuid.UUID(str(product_id))
        except (ValueError, TypeError):
            return None

        return Product.objects.filter(
            id=product_id,
            status=Product.ProductStatus.AVAILABLE,
            stock__gt=0,
            vendor__status='ACTIVE',
            vendor__locations__is_active=True
        ).first()

    @staticmethod
    def get_manageable_products(user, vendor_id: str = None) -> QuerySet[Product]:
        """
        Retrieves products that a specific user can manage in their dashboard.
        - Admins/Superusers see everything.
        - Vendors see their own products.
        - Others see nothing.
        """
        if not user.is_authenticated:
            return Product.objects.none()

        queryset = Product.objects.all().order_by('-created_at')

        if user.role == UserRoles.ADMIN or user.is_superuser:
            if vendor_id:
                try:
                    uuid.UUID(str(vendor_id))
                    queryset = queryset.filter(vendor_id=vendor_id)
                except: pass
            return queryset
            
        if user.role == UserRoles.VENDEDOR:
            return queryset.filter(vendor=user)

        return Product.objects.none()
