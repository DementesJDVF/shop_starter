from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.serializers.search_serializer import (
    AISearchRequestSerializer,
    AISearchResponseSerializer,
)
from services.ai_service import AIService
from services.search_ai_service import SearchAIService


class AISearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AISearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        search_service = SearchAIService(ai_service=AIService())
        result = search_service.search(
            query=serializer.validated_data["query"],
            user_location=serializer.validated_data["user_location"],
        )

        response_serializer = AISearchResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
