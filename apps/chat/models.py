from django.db import models
from django.conf import settings
from apps.core.models import BaseModel
from apps.products.models import Product

class AIRecommendationEvent(BaseModel):
    """
    Registra cuando la IA recomienda un producto a un usuario.
    Permite al vendedor auditar y ver los historiales.
    """
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_interactions",
        help_text="El comprador que chateó con el asistente."
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="ai_recommendations",
        help_text="El producto recomendado."
    )
    user_query = models.TextField(
        help_text="La frase o contexto que el usuario proveyó (ej: 'busco zapatillas baratas')."
    )
    ai_reasoning = models.TextField(
        null=True, 
        blank=True,
        help_text="Opcional. Explicación breve de por qué la IA recomendó esto."
    )

    class Meta:
        db_table = "chat_ai_recommendation_event"
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["buyer"]),
        ]

    def __str__(self):
        return f"Recomendación de {self.product.name} a {self.buyer.username if self.buyer else 'Anónimo'}"
