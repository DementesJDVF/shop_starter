from django.contrib import admin
from .models import AIRecommendationEvent

@admin.register(AIRecommendationEvent)
class AIRecommendationEventAdmin(admin.ModelAdmin):
    list_display = ("product", "buyer", "created_at")
    list_filter = ("product", "created_at")
    search_fields = ("user_query", "ai_reasoning")
    readonly_fields = ("created_at",)
