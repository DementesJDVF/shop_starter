from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    def perform_create(self, serializer):
        serializer.save()
