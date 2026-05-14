from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.terms.selectors import get_latest_acceptance, get_terms_content
from apps.terms.serializers import (
    TermsAcceptanceSerializer,
    TermsContentSerializer,
    TermsStatusSerializer,
)
from apps.terms.services import (
    get_current_terms_version,
    has_accepted_terms,
    register_terms_acceptance,
)


class TermsContentView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        version = request.query_params.get("version") or get_current_terms_version()
        serializer = TermsContentSerializer(
            {
                "version": version,
                "content": get_terms_content(version),
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TermsAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TermsAcceptanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        version = serializer.validated_data.get("version") or get_current_terms_version()
        acceptance = register_terms_acceptance(request.user, version)

        return Response(
            TermsAcceptanceSerializer(acceptance).data,
            status=status.HTTP_201_CREATED,
        )


class TermsStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        version = request.query_params.get("version") or get_current_terms_version()
        latest_acceptance = get_latest_acceptance(request.user)
        accepted = has_accepted_terms(request.user, version)
        accepted_at = latest_acceptance.accepted_at if latest_acceptance and accepted else None

        serializer = TermsStatusSerializer(
            {
                "version": version,
                "accepted": accepted,
                "accepted_at": accepted_at,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
