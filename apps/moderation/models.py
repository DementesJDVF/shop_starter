import uuid

from django.db import models


class ModerationFlag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        REVIEWED = "REVIEWED", "Reviewed"
        DISMISSED = "DISMISSED", "Dismissed"

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="moderation_flags",
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "moderation_flag"

    def __str__(self):
        return f"{self.product} - {self.status}"
