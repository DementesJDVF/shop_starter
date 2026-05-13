from django.apps import AppConfig


class TermsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.terms"

    def ready(self):
        from apps.terms.services import install_terms_auth_hooks

        install_terms_auth_hooks()
