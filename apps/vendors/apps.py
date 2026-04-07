from django.apps import AppConfig


class VendorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vendors"


    def ready(self):
        # Register vendor domain signals.
        from . import signals  # noqa: F401
        import apps.vendors.signals