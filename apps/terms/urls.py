from django.urls import path

from apps.terms.views import TermsAcceptView, TermsContentView, TermsStatusView


urlpatterns = [
    path("", TermsContentView.as_view(), name="terms-content"),
    path("accept/", TermsAcceptView.as_view(), name="terms-accept"),
    path("status/", TermsStatusView.as_view(), name="terms-status"),
]
