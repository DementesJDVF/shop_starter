"""Serializers for product endpoints."""
from rest_framework import serializers
from apps.products.models import Product, PImages, Category
from apps.users.models import User
from apps.users.constants import UserRoles
from apps.vendors.models import VendorProfile
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'is_active']
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PImages
        fields = ['id', 'url_image', 'is_main'] # Lo que querés recibir/mandar
class CreProSerializer(serializers.ModelSerializer):
    # Aquí está la magia: filtramos el queryset para que la API 
    # rechace cualquier ID que no pertenezca a un vendedor.
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRoles.VENDOR))
    #vendor = serializers.PrimaryKeyRelatedField(queryset=VendorProfile.objects.all())
    # Para LEER: Muestra el objeto completo de la categoría
    category_detail = CategorySerializer(source='category', read_only=True)
    # Para ESCRIBIR: Permite mandar solo el ID
    # 'queryset' es necesario para que DRF valide que la categoría existe
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    # 'images' debe coincidir con el related_name del ForeignKey en ProductImage
    images = ProductImageSerializer(many=True, read_only=False)
    class Meta:
        model = Product
        fields = '__all__'
        """
        fields = [
            'id', 'vendor', 'category', 'category_detail', 'name', 
            'description', 'price', 'stock', 'status', 'is_featured', 'images']
        """
    # Para que DRF sepa qué hacer con el array al crear el producto
    def create(self, validated_data):
        images_data = validated_data.pop('images', []) # Sacamos las imágenes del paquete
        product = Product.objects.create(**validated_data) # Creamos el producto solo
        # Ahora creamos cada imagen asociada a ese producto
        for image_data in images_data:
            PImages.objects.create(product=product, **image_data)
        return product
class ProductCreateSerializer(serializers.Serializer):
    """Serializer for product create/update payloads."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock = serializers.IntegerField(required=False, min_value=0)

    def validate_price(self, value):
        """Ensure product price is greater than zero."""
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0")
        return value
class ProductSerializer(serializers.ModelSerializer):
    """Read serializer for products."""
    class Meta:
        model = Product
        fields = [
            "id",
            "vendor",
            "name",
            "description",
            "price",
            "stock",
            "status",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "vendor", "status", "created_at", "updated_at", "is_deleted"]
