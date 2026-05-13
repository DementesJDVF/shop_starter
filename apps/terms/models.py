from django.conf import settings
from django.db import models


class TermsAcceptance(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="terms_acceptances",
    )
    accepted_at = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=50)

    class Meta:
        db_table = "terms_acceptance"
        ordering = ["-accepted_at"]
        indexes = [
            models.Index(fields=["user", "version"], name="terms_user_version_idx"),
            models.Index(fields=["accepted_at"], name="terms_accepted_at_idx"),
        ]

    def __str__(self):
        return f"{self.user_id} accepted {self.version} at {self.accepted_at}"


class TermsContent(models.Model):
    version = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "terms_content"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["version", "is_active"], name="terms_content_active_idx"),
        ]

    def __str__(self):
        return self.content or ""
