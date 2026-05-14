from django.conf import settings
from django.db import transaction
from rest_framework import exceptions, serializers

from apps.terms.models import TermsAcceptance


_TERMS_HOOKS_INSTALLED = False


def get_current_terms_version():
    return getattr(settings, "SHOPSTARTER_TERMS_VERSION", "v1")


@transaction.atomic
def register_terms_acceptance(user, version):
    acceptance = TermsAcceptance.objects.create(user=user, version=version)

    if hasattr(user, "terms_accepted") and not user.terms_accepted:
        user.terms_accepted = True
        user.save(update_fields=["terms_accepted"])

    return acceptance


def has_accepted_terms(user, version):
    if not user or not getattr(user, "is_authenticated", False):
        return False

    return TermsAcceptance.objects.filter(user=user, version=version).exists()


def _request_accepts_terms(initial_data):
    accepted = initial_data.get("terms_accepted", initial_data.get("accept_terms", False))
    return accepted in (True, "true", "True", "1", 1, "on", "yes", "YES")


def _requested_terms_version(initial_data):
    return initial_data.get("terms_version") or initial_data.get("version") or get_current_terms_version()


def _ensure_terms_for_user(user, version):
    if has_accepted_terms(user, version):
        return

    if getattr(user, "terms_accepted", False):
        register_terms_acceptance(user, version)
        return

    raise exceptions.PermissionDenied("Debes aceptar los términos y condiciones vigentes para continuar.")


def install_terms_auth_hooks():
    global _TERMS_HOOKS_INSTALLED
    if _TERMS_HOOKS_INSTALLED:
        return

    _TERMS_HOOKS_INSTALLED = True
    _patch_register_serializer()
    _patch_login_serializer()
    _patch_user_service()
    _patch_auth_service()


def _patch_register_serializer():
    from apps.users.serializers import RegisterSerializer

    if getattr(RegisterSerializer, "_terms_hooked", False):
        return

    original_validate = RegisterSerializer.validate

    def validate(self, attrs):
        attrs = original_validate(self, attrs)
        if not _request_accepts_terms(self.initial_data):
            raise serializers.ValidationError(
                {"terms_accepted": "Debes aceptar los términos y condiciones para registrarte."}
            )

        attrs["terms_accepted"] = True
        attrs["terms_version"] = _requested_terms_version(self.initial_data)
        return attrs

    RegisterSerializer.validate = validate
    RegisterSerializer._terms_hooked = True


def _patch_login_serializer():
    from apps.users.serializers import LoginSerializer

    if getattr(LoginSerializer, "_terms_hooked", False):
        return

    original_validate = LoginSerializer.validate

    def validate(self, data):
        data = original_validate(self, data)
        user = data["user"]
        version = _requested_terms_version(self.initial_data)

        if _request_accepts_terms(self.initial_data):
            if not has_accepted_terms(user, version):
                register_terms_acceptance(user, version)
        else:
            _ensure_terms_for_user(user, version)

        return data

    LoginSerializer.validate = validate
    LoginSerializer._terms_hooked = True


def _patch_user_service():
    from apps.users.application.services import UserService

    if getattr(UserService, "_terms_hooked", False):
        return

    original_register_user = UserService.register_user

    @staticmethod
    @transaction.atomic
    def register_user(*, validated_data, ip_address=None):
        version = validated_data.get("terms_version") or get_current_terms_version()
        if not validated_data.get("terms_accepted"):
            raise exceptions.PermissionDenied("Debes aceptar los términos y condiciones para registrarte.")

        user = original_register_user(validated_data=validated_data, ip_address=ip_address)
        register_terms_acceptance(user, version)
        return user

    UserService.register_user = register_user
    UserService._terms_hooked = True


def _patch_auth_service():
    from apps.users.services.auth_service import AuthService

    if getattr(AuthService, "_terms_hooked", False):
        return

    original_login_user = AuthService.login_user

    @staticmethod
    def login_user(user, ip_address, user_agent):
        _ensure_terms_for_user(user, get_current_terms_version())
        return original_login_user(user=user, ip_address=ip_address, user_agent=user_agent)

    AuthService.login_user = login_user
    AuthService._terms_hooked = True
