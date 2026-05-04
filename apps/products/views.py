from rest_framework import status, viewsets
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.decorators import api_view, permission_classes, action, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from apps.users.permissions import IsVendor
from apps.products.models import Product, Category
from apps.products.serializers import (CreProSerializer,
                                       ReadProSerializer,
                                       CategorySerializer,
                                       ProductSerializer)
from apps.core.services.email_service import send_product_status_notification
from apps.core.models import Notification
from apps.ai.services.ai_service import generate_product_description
from apps.products.services import ProductService
from rest_framework import generics
import logging

logger = logging.getLogger(__name__)

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductViewSet(viewsets.ModelViewSet):
    throttle_scope = None

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReadProSerializer
        return CreProSerializer
    
    pagination_class = ProductPagination
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']

    def get_queryset(self):
        user = self.request.user
        vendor_id = self.request.query_params.get('vendor')
        
        if user.is_authenticated:
            return ProductService.get_manageable_products(user, vendor_id=vendor_id)
        
        return ProductService.get_public_catalog(vendor_id=vendor_id)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied, ValidationError
        user = self.request.user
        
        if user.role == "ADMIN" or user.is_superuser:
            vendor_id = self.request.data.get('vendor')
            if vendor_id:
                from apps.users.models import User
                try:
                    vendor = User.objects.get(id=vendor_id, role="VENDEDOR")
                    serializer.save(vendor=vendor)
                except User.DoesNotExist:
                    raise ValidationError({"vendor": "El vendedor especificado no existe o no tiene rol VENDEDOR."})
            else:
                serializer.save(vendor=user)
            return

        if user.role == "VENDEDOR":
            serializer.save(vendor=user)
        else:
            raise PermissionDenied("Solo los vendedores o administradores pueden crear productos.")

    def perform_update(self, serializer):
        from rest_framework.exceptions import PermissionDenied
        user = self.request.user
        
        old_instance = self.get_object()
        old_status = old_instance.status
        new_status = serializer.validated_data.get('status', old_status)
        
        if old_status == "PENDING" and new_status in [Product.ProductStatus.AVAILABLE, "REJECTED"]:
            if user.role != 'ADMIN' and not user.is_superuser:
                raise PermissionDenied("Solo los administradores pueden aprobar o rechazar productos.")
        
        if user.role == 'VENDEDOR' and old_status != new_status:
             if new_status == Product.ProductStatus.AVAILABLE and old_status in ['PENDING', 'REJECTED']:
                 raise PermissionDenied("No tienes permiso para auto-aprobar productos.")

        instance = serializer.save()
        
        if old_status != instance.status:
            if instance.status in ["AVAILABLE", "REJECTED"]:
                send_product_status_notification(instance)
            
            status_label = "Aprobado" if instance.status == "AVAILABLE" else "Rechazado"
            reason_text = f"\nMotivo: {instance.rejection_reason}" if instance.status == "REJECTED" and instance.rejection_reason else ""
            
            Notification.objects.create(
                user=instance.vendor,
                title=f"Producto {status_label}",
                message=f"Tu producto '{instance.name}' ha sido {status_label.lower()}.{reason_text}",
                type="PRODUCT_STATUS"
            )

    def create(self, request, *args, **kwargs):
        import traceback
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except Exception as e:
            logger.error(f"ERROR COMPLETO EN CREATE:\n{traceback.format_exc()}")
            return Response(
                {"debug_error": str(e), "trace": traceback.format_exc()},
                status=500
            )
        
        read_serializer = ReadProSerializer(serializer.instance, context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Soft Delete: cambia el estado a INACTIVE y activa is_deleted."""
        instance = self.get_object()
        
        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            if instance.vendor != request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permisos para borrar este producto.")

        instance.status = Product.ProductStatus.INACTIVE
        instance.delete()
        
        logging.getLogger(__name__).info(f"[AUDIT] Producto {instance.id} archivado (Soft Delete) por {request.user.username}.")
        
        return Response({"message": "Producto archivado (desactivado) exitosamente."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def restore(self, request, pk=None):
        """Restaura un producto archivado (Soft Delete -> Active)."""
        instance = Product.all_objects.get(pk=pk)
        
        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            if instance.vendor != request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No tienes permisos para restaurar este producto.")

        instance.restore()
        return Response({"message": "Producto restaurado exitosamente."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], throttle_classes=[ScopedRateThrottle], throttle_scope='ia_limit')
    def generate_ai_description(self, request, pk=None):
        from rest_framework.exceptions import PermissionDenied
        
        product = self.get_object()
        
        if (request.user.role not in ['VENDEDOR', 'ADMIN'] and not request.user.is_superuser) or (request.user.role == 'VENDEDOR' and product.vendor != request.user):
            raise PermissionDenied("No tienes permisos para generar una descripción IA para este producto.")
            
        if product.ai_description:
            return Response({"ai_description": product.ai_description, "cached": True})
            
        main_image = product.images.filter(is_main=True).first()
        if not main_image:
            main_image = product.images.first()
            
        if not main_image or not main_image.url_image:
            return Response({"error": "No hay imágenes disponibles para analizar."}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.products.tasks import generate_ai_description_task
        source_url = main_image.url_image.url if hasattr(main_image.url_image, 'url') else main_image.url_image
        
        try:
            if not source_url.startswith('http'):
                from django.conf import settings
                backend_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000').rstrip('/')
                source_url = f"{backend_url}{'' if source_url.startswith('/') else '/'}{source_url}"
            
            task = generate_ai_description_task.delay(product.id, source_url, is_url=True)
            
            product.ai_status = Product.AIStatus.PROCESSING
            product.save(update_fields=['ai_status'])

            return Response({
                "status": "PROCESSING",
                "task_id": task.id,
                "message": "La IA ha comenzado a analizar el producto en segundo plano.",
                "cached": False
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            product.ai_status = Product.AIStatus.FAILED
            product.save(update_fields=['ai_status'])
            logger.error(f"[SRE] Error en generación directa de IA: {str(e)}")
            return Response({"error": f"Error en el motor de IA: {str(e)}"}, status=500)

    # ✅ CORREGIDO: suggest_description ahora es su propio método @action
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def suggest_description(self, request):
        """
        Sugiere una descripción basada en una imagen (URL o archivo).
        Modo Directo (Síncrono) para máxima confiabilidad.
        """
        image_url = request.data.get('image_url')
        image_file = request.FILES.get('image_file')

        # 1. Validación de entrada
        source = image_file if image_file else image_url
        is_url = bool(image_url and not image_file)

        if not source:
            return Response({"error": "Se requiere una imagen (URL o archivo)."}, status=400)

        try:
            suggestion = generate_product_description(source, is_url=is_url)

            return Response({
                "status": "DONE",
                "result": suggestion,
                "message": "Sugerencia generada correctamente (Modo Directo)."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"[SRE] Error crítico en sugerencia IA síncrona: {str(e)}")
            return Response({"error": f"Error en el motor de IA: {str(e)}"}, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def review_full_product(self, request):
        """
        Admin REVISA COMPLETAMENTE un producto rechazado.
        Decide si fue falso positivo o legítimamente inapropiado.
        """
        from rest_framework.exceptions import PermissionDenied
        from apps.moderation.models import ProductReview, RejectedImage
        from apps.products.models import PImages
        from django.utils import timezone

        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            raise PermissionDenied("Solo los administradores pueden revisar productos.")

        product_review_id = request.data.get('product_review_id')
        decision = request.data.get('decision')  # 'APPROVED_PRODUCT' | 'REJECTED_PRODUCT' | 'APPROVED_IMAGES'
        notes = request.data.get('notes', '')

        if not product_review_id or not decision:
            return Response(
                {'error': 'product_review_id y decision son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if decision not in ['APPROVED_PRODUCT', 'REJECTED_PRODUCT', 'APPROVED_IMAGES']:
            return Response(
                {'error': 'decision debe ser: APPROVED_PRODUCT, REJECTED_PRODUCT o APPROVED_IMAGES'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product_review = ProductReview.objects.get(id=product_review_id)

            if product_review.review_status != ProductReview.ReviewStatus.PENDING:
                return Response(
                    {'error': 'Este producto ya fue revisado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product = product_review.product
            logger.info(f"Admin {request.user.username} revisa producto completo: {product.name} - Decisión: {decision}")

            if decision == 'APPROVED_PRODUCT':
                PImages.objects.filter(product=product).update(
                    moderation_status=PImages.ModerationStatus.APPROVED
                )
                Product.objects.filter(pk=product.pk).update(
                    status=Product.ProductStatus.AVAILABLE,
                    rejection_reason=""
                )
                RejectedImage.objects.filter(product=product).update(
                    review_status=RejectedImage.ReviewStatus.APPROVED
                )
                product_review.review_status = ProductReview.ReviewStatus.APPROVED_PRODUCT

            elif decision == 'REJECTED_PRODUCT':
                Product.objects.filter(pk=product.pk).update(
                    status=Product.ProductStatus.REJECTED,
                    rejection_reason=notes or "Producto rechazado tras revisión manual: contenido inapropiado"
                )
                RejectedImage.objects.filter(product=product).update(
                    review_status=RejectedImage.ReviewStatus.CONFIRMED_REJECTED
                )
                product_review.review_status = ProductReview.ReviewStatus.REJECTED_PRODUCT

            elif decision == 'APPROVED_IMAGES':
                PImages.objects.filter(product=product).update(
                    moderation_status=PImages.ModerationStatus.APPROVED
                )
                Product.objects.filter(pk=product.pk).update(
                    status=Product.ProductStatus.AVAILABLE,
                    rejection_reason=""
                )
                RejectedImage.objects.filter(product=product).update(
                    review_status=RejectedImage.ReviewStatus.APPROVED
                )
                product_review.review_status = ProductReview.ReviewStatus.APPROVED_IMAGES

            product_review.reviewed_by = request.user
            product_review.reviewed_at = timezone.now()
            product_review.admin_notes = notes
            product_review.save()

            try:
                product.refresh_from_db()
                send_product_status_notification(product)
            except Exception as e:
                logger.warning(f"Error enviando email de decisión: {e}")

            from apps.moderation.serializers import ProductReviewDetailSerializer
            return Response(
                ProductReviewDetailSerializer(product_review).data,
                status=status.HTTP_200_OK
            )

        except ProductReview.DoesNotExist:
            return Response(
                {'error': 'ProductReview no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error revisando producto: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='tasks/(?P<task_id>[^/.]+)')
    def get_task_status(self, request, task_id=None):
        """
        Endpoint para consultar el estado de una tarea de Celery por su ID.
        """
        try:
            from celery.result import AsyncResult
            res = AsyncResult(task_id)
            
            state = res.state
            
            if state == 'SUCCESS':
                return Response({
                    "status": "DONE",
                    "result": res.result
                })
            elif state in ['FAILURE', 'REVOKED']:
                return Response({
                    "status": "FAILED",
                    "error": str(res.result) or "La tarea fue cancelada o falló."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif state == 'RETRY':
                return Response({"status": "RETRYING"})
            elif state == 'STARTED':
                return Response({"status": "PROCESSING"})
            
            return Response({"status": "PENDING"})
            
        except Exception as e:
            logger.error(f"[SRE] Error al consultar tarea {task_id}: {str(e)}")
            return Response({"error": "No se pudo consultar el estado de la tarea."}, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def approve_rejected_image(self, request):
        """
        Admin aprueba una imagen rechazada (falso positivo).
        Si todas las imágenes aprueban → Producto pasa a AVAILABLE.
        """
        from rest_framework.exceptions import PermissionDenied
        from apps.moderation.models import RejectedImage
        from apps.products.models import PImages
        from django.utils import timezone

        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            raise PermissionDenied("Solo los administradores pueden revisar imágenes.")

        image_id = request.data.get('image_id')
        notes = request.data.get('notes', '')

        if not image_id:
            return Response({'error': 'image_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rejected = RejectedImage.objects.get(id=image_id)

            if rejected.review_status != RejectedImage.ReviewStatus.PENDING:
                return Response(
                    {'error': 'Solo se pueden revisar imágenes pendientes'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            rejected.review_status = RejectedImage.ReviewStatus.APPROVED
            rejected.reviewed_by = request.user
            rejected.reviewed_at = timezone.now()
            rejected.admin_notes = notes
            rejected.save()

            PImages.objects.filter(pk=rejected.image.pk).update(
                moderation_status=PImages.ModerationStatus.APPROVED
            )

            product = rejected.product
            all_approved = all(
                img.moderation_status == PImages.ModerationStatus.APPROVED
                for img in product.images.all()
            )

            if all_approved and product.status == Product.ProductStatus.REJECTED:
                Product.objects.filter(pk=product.pk).update(
                    status=Product.ProductStatus.AVAILABLE,
                    rejection_reason=""
                )
                try:
                    product.refresh_from_db()
                    send_product_status_notification(product)
                except Exception as e:
                    logger.warning(f"Error enviando email de aprobación: {e}")

            from apps.moderation.serializers import RejectedImageDetailSerializer
            return Response(
                RejectedImageDetailSerializer(rejected).data,
                status=status.HTTP_200_OK
            )

        except RejectedImage.DoesNotExist:
            return Response({'error': 'Imagen rechazada no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error aprobando imagen: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def confirm_rejected_image(self, request):
        """
        Admin confirma el rechazo de una imagen (contenido definitivamente inapropiado).
        """
        from rest_framework.exceptions import PermissionDenied
        from apps.moderation.models import RejectedImage
        from django.utils import timezone

        if request.user.role != 'ADMIN' and not request.user.is_superuser:
            raise PermissionDenied("Solo los administradores pueden revisar imágenes.")

        image_id = request.data.get('image_id')
        notes = request.data.get('notes', '')

        if not image_id:
            return Response({'error': 'image_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rejected = RejectedImage.objects.get(id=image_id)

            if rejected.review_status != RejectedImage.ReviewStatus.PENDING:
                return Response(
                    {'error': 'Solo se pueden revisar imágenes pendientes'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            rejected.review_status = RejectedImage.ReviewStatus.CONFIRMED_REJECTED
            rejected.reviewed_by = request.user
            rejected.reviewed_at = timezone.now()
            rejected.admin_notes = notes
            rejected.save()

            from apps.moderation.serializers import RejectedImageDetailSerializer
            return Response(
                RejectedImageDetailSerializer(rejected).data,
                status=status.HTTP_200_OK
            )

        except RejectedImage.DoesNotExist:
            return Response({'error': 'Imagen rechazada no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error confirmando rechazo: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductCatalogView(generics.ListAPIView):
    """
    Public endpoint for listing active products from active vendors.
    """
    serializer_class = ReadProSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    filterset_fields = ['category']
    search_fields = ['name', 'description']

    def get_queryset(self):
        vendor_id = self.request.query_params.get('vendor')
        user = self.request.user
        
        if user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser):
             return ProductService.get_manageable_products(user, vendor_id=vendor_id)
             
        return ProductService.get_public_catalog(vendor_id=vendor_id)


class ProductDetailPublicView(generics.RetrieveAPIView):
    """
    Public endpoint for retrieving a single active product detail.
    """
    serializer_class = ReadProSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    lookup_field = 'id'

    def get_queryset(self):
        return Product.objects.filter(
            status=Product.ProductStatus.AVAILABLE,
            vendor__status='ACTIVE'
        )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        from apps.users.permissions import IsAdmin
        return [IsAdmin()]

    def perform_create(self, serializer):
        serializer.save()


class CategoryViewGet(viewsets.ReadOnlyModelViewSet):
    """
    Vista simple para ver la lista de categorías y el detalle de cada una.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    lookup_field = 'id'


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def nearby_products(request):
    request.throttle_scope = 'anon'
    from apps.geo.models import Location
    from apps.geo.utils import haversine
    
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius", 5)

    try:
        lat = float(lat)
        lng = float(lng)
        radius = float(radius)
    except:
        return Response([], status=400)

    from django.db.models.expressions import RawSQL
    query = """
        6371 * acos(
            cos(radians(%s)) * cos(radians(latitude)) *
            cos(radians(longitude) - radians(%s)) +
            sin(radians(%s)) * sin(radians(latitude))
        )
    """

    locations = Location.objects.select_related("user").filter(
        user__status='ACTIVE',
        user__role='VENDEDOR',
        is_active=True
    ).annotate(
        distance=RawSQL(query, (lat, lng, lat))
    ).filter(distance__lte=radius)

    nearby_user_ids = []
    user_distances = {}

    for loc in locations:
        nearby_user_ids.append(loc.user.id)
        user_distances[loc.user.id] = round(loc.distance, 2)

    products = Product.objects.filter(
        vendor__in=nearby_user_ids,
        status=Product.ProductStatus.AVAILABLE
    ).select_related('category', 'vendor').prefetch_related('images')

    data = []
    for product in products:
        prod_data = ReadProSerializer(product, context={'request': request}).data
        prod_data['distance'] = user_distances.get(product.vendor.id)
        data.append(prod_data)

    data.sort(key=lambda x: x['distance'] if x['distance'] is not None else 999)

    return Response(data)