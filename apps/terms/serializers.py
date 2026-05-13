from rest_framework import serializers

from apps.terms.models import TermsAcceptance
from apps.terms.services import get_current_terms_version


class TermsAcceptanceSerializer(serializers.ModelSerializer):
    version = serializers.CharField(required=False)

    class Meta:
        model = TermsAcceptance
        fields = ["id", "version", "accepted_at"]
        read_only_fields = ["id", "accepted_at"]

    def validate_version(self, value):
        return value or get_current_terms_version()


class TermsContentSerializer(serializers.Serializer):
    version = serializers.CharField()
    content = serializers.CharField()


class TermsStatusSerializer(serializers.Serializer):
    version = serializers.CharField()
    accepted = serializers.BooleanField()
    accepted_at = serializers.DateTimeField(allow_null=True)
