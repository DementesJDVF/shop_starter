from apps.audit.infrastructure.models import AuditLog


class AuditRepository:

    @staticmethod
    def create(**kwargs):
        return AuditLog.objects.create(**kwargs)
