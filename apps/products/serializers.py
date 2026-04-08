"""Serializers for product endpoints."""

from rest_framework import serializers
from apps.products.models import Category, Product, PImages, PComments
from apps.users.models import User
from apps.users.constants import UserRoles
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active"]
class PImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PImages
        fields = ["id", "url_image", "is_main"]  # Lo que querés recibir/mandar
class ProductSerializer(serializers.ModelSerializer):
    # Aquí está la magia: filtramos el queryset para que la API
    # rechace cualquier ID que no pertenezca a un vendedor.
    # vendor = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=UserRoles.VENDOR))
    vendor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # Para LEER: Muestra el objeto completo de la categoría
    category_detail = CategorySerializer(source="category", read_only=True)
    # Para ESCRIBIR: Permite mandar solo el ID
    # 'queryset' es necesario para que DRF valide que la categoría existe
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    # 'images' debe coincidir con el related_name del ForeignKey en ProductImage
    images = PImageSerializer(many=True, required=False)
    class Meta:
        model = Product
        fields = "__all__"
    def validate_images(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("Se permiten máximo 10 imágenes.")
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
class PCommentSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = PComments
        fields = "__all__"