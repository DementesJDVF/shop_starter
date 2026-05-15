from rest_framework import serializers
from .models import RejectedImage, ModerationFlag, ProductReview


class RejectedImageSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.get_full_name', read_only=True)
    vendor_email = serializers.CharField(source='vendor.email', read_only=True)
    image_url = serializers.CharField(source='image.url_image', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = RejectedImage
        fields = [
            'id',
            'product_name',
            'vendor_name',
            'vendor_email',
            'image_url',
            'ai_reason',
            'ai_confidence',
            'review_status',
            'reviewed_by_name',
            'rejected_at',
            'reviewed_at',
        ]
        read_only_fields = fields


class RejectedImageDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para lectura individual."""
    product_details = serializers.SerializerMethodField()
    vendor_details = serializers.SerializerMethodField()
    image_details = serializers.SerializerMethodField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = RejectedImage
        fields = [
            'id',
            'product_details',
            'vendor_details',
            'image_details',
            'ai_reason',
            'ai_confidence',
            'review_status',
            'reviewed_by_name',
            'admin_notes',
            'rejected_at',
            'reviewed_at',
        ]
        read_only_fields = fields

    def get_product_details(self, obj):
        return {
            'id': obj.product.id,
            'name': obj.product.name,
            'category': ', '.join([c.name for c in obj.product.categories.all()]) if obj.product.categories.exists() else None,
            'price': str(obj.product.price),
            'status': obj.product.status,
            'description': obj.product.description[:200],  # primeros 200 chars
        }

    def get_vendor_details(self, obj):
        return {
            'id': obj.vendor.id,
            'name': obj.vendor.get_full_name() or obj.vendor.username,
            'email': obj.vendor.email,
            'username': obj.vendor.username,
        }

    def get_image_details(self, obj):
        return {
            'id': obj.image.id,
            'url': obj.image.url_image,
            'is_main': obj.image.is_main,
            'moderation_status': obj.image.moderation_status,
            'created_at': obj.image.date_created,
        }


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer para revisión completa de producto."""
    vendor_name = serializers.CharField(source='vendor.get_full_name', read_only=True)
    vendor_email = serializers.CharField(source='vendor.email', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = ProductReview
        fields = [
            'id',
            'product',
            'vendor_name',
            'vendor_email',
            'rejected_images_count',
            'review_status',
            'reviewed_by_name',
            'content_issues',
            'created_at',
            'reviewed_at',
        ]
        read_only_fields = ['id', 'created_at']


class ProductReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado con información completa del producto."""
    product_details = serializers.SerializerMethodField()
    vendor_details = serializers.SerializerMethodField()
    images_details = serializers.SerializerMethodField()
    rejected_images = serializers.SerializerMethodField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = ProductReview
        fields = [
            'id',
            'product_details',
            'vendor_details',
            'images_details',
            'rejected_images',
            'rejected_images_count',
            'review_status',
            'reviewed_by_name',
            'admin_notes',
            'content_issues',
            'created_at',
            'reviewed_at',
        ]
        read_only_fields = fields

    def get_product_details(self, obj):
        product = obj.product
        return {
            'id': str(product.id),
            'name': product.name,
            'description': product.description,
            'category': ', '.join([c.name for c in product.categories.all()]) if product.categories.exists() else None,
            'price': str(product.price),
            'stock': product.stock,
            'status': product.status,
            'created_at': product.created_at.isoformat() if product.created_at else None,
        }

    def get_vendor_details(self, obj):
        vendor = obj.vendor
        return {
            'id': str(vendor.id),
            'name': vendor.get_full_name() or vendor.username,
            'email': vendor.email,
            'username': vendor.username,
            'phone': getattr(vendor, 'phone', None),
        }

    def get_images_details(self, obj):
        images = obj.product.images.all()
        return [
            {
                'id': str(img.id),
                'url': str(img.url_image),
                'is_main': img.is_main,
                'moderation_status': img.moderation_status,
                'is_rejected': img.moderation_status == 'REJECTED',
            }
            for img in images
        ]

    def get_rejected_images(self, obj):
        rejected = RejectedImage.objects.filter(product=obj.product)
        return [
            {
                'id': str(r.id),
                'image_url': str(r.image.url_image),
                'ai_reason': r.ai_reason,
                'ai_confidence': r.ai_confidence,
                'image_status': r.review_status,
            }
            for r in rejected
        ]


class ModerationFlagSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ModerationFlag
        fields = ['id', 'product_name', 'reason', 'status', 'created_at']