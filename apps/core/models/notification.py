import uuid
from django.db import models
from django.conf import settings
from .base import BaseModel

class Notification(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Optional: type to distinguish between order, product approval, etc.
    type = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = "core_notification"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
