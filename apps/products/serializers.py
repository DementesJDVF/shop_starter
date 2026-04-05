"""Serializers for product endpoints."""

from rest_framework import serializers
from apps.products.models import Product, PImages, Category
from apps.users.models import User
from apps.users.constants import UserRoles


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PImages
        fields = ["id", "url_image", "is_main"]  # Lo que querés recibir/mandar


class ProductImageInputSerializer(serializers.Serializer):
    url_image = serializers.URLField(max_length=500)
    is_main = serializers.BooleanField(default=False)


class CreProSerializer(serializers.ModelSerializer):
    # Aquí está la magia: filtramos el queryset para que la API
    # rechace cualquier ID que no pertenezca a un vendedor.
    vendor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # vendor = serializers.PrimaryKeyRelatedField(queryset=VendorProfile.objects.all())
    # Para LEER: Muestra el objeto completo de la categoría
    category_detail = CategorySerializer(source="category", read_only=True)
    # Para ESCRIBIR: Permite mandar solo el ID
    # 'queryset' es necesario para que DRF valide que la categoría existe
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    # 'images' debe coincidir con el related_name del ForeignKey en ProductImage
    images = ProductImageInputSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = "__all__"
        """
        #No se usa.
        fields = [
            'id', 'vendor', 'category', 'category_detail', 'name', 
            'description', 'price', 'stock', 'status', 'is_featured', 'images']
        """

    def validate_images(self, value):
        if len(value) > 2:
            raise serializers.ValidationError("Se permiten máximo 2 imágenes.")
        mains = [img for img in value if img.get("is_main")]
        if len(mains) > 1:
            raise serializers.ValidationError("Solo una imagen puede ser la principal.")
        return value

    # Para que DRF sepa qué hacer con el array al crear el producto
    def create(self, validated_data):
        images_data = validated_data.pop(
            "images", []
        )  # Sacamos las imágenes del paquete
        product = Product.objects.create(**validated_data)  # Creamos el producto solo
        # Ahora creamos cada imagen asociada a ese producto
        for image_data in images_data:
            PImages.objects.create(product=product, **image_data)
        return product


class ReadProSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source="vendor.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    # 1. Agregamos el campo de imágenes.
    # El nombre 'images' debe coincidir con el related_name que pusiste en el modelo ProductImage.
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "status",
            "vendor_name",
            "category_name",
            "is_featured",
            "images",  # 2. Lo incluimos en la lista de campos
            "created_at",
        ]
        read_only_fields = fields
