import time
import requests
from django.urls import reverse
from rest_framework.test import APITestCase
from apps.users.models import User
from apps.products.models import Product, ProductImage

class AIStressTests(APITestCase):
    """
    PRUEBAS DE CARGA PARA EL MOTOR DE IA:
    Valida que la cola de Celery gestione correctamente múltiples peticiones 
    simultáneas de generación de descripciones sin bloquear el API.
    """
    def setUp(self):
        self.admin = User.objects.create_superuser('admin_stress', 'admin@test.com', 'Pass123!')
        self.vendor = User.objects.create_user('vendor_stress', 'vendor@test.com', 'Pass123!', role='VENDEDOR')
        
        # Crear 10 productos para procesar en masa
        self.products = []
        for i in range(10):
            p = Product.objects.create(
                name=f"Stress Product {i}",
                description="Original description",
                price=100,
                vendor=self.vendor,
                status='AVAILABLE'
            )
            ProductImage.objects.create(
                product=p,
                url_image="https://picsum.photos/200/300", # URL dummy para análisis
                is_main=True
            )
            self.products.append(p)
            
        self.client.force_authenticate(user=self.admin)

    def test_mass_ai_generation_async(self):
        """Simula 10 peticiones rápidas de IA y valida que todas entren en cola."""
        task_ids = []
        start_time = time.time()
        
        for p in self.products:
            url = reverse('product-ai-gen', kwargs={'pk': p.pk})
            response = self.client.post(url)
            self.assertEqual(response.status_code, 202) # ACCEPTED
            task_ids.append(response.data['task_id'])
            
        end_time = time.time()
        
        # El API debe responder casi instantáneamente (< 1 seg para 10 peticiones)
        # porque el trabajo pesado es asíncrono.
        self.assertLess(end_time - start_time, 2.0)
        print(f"DEBUG STRESS: 10 tareas encoladas en {end_time - start_time:.2f}s")

        # Verificar que los productos están en estado PROCESSING
        for p in self.products:
            p.refresh_from_db()
            self.assertEqual(p.ai_status, 'PROCESSING')
