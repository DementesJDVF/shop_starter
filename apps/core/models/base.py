from django.db import models
from .managers import SoftDeleteManager


class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["is_deleted"]),
        ]

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])

    def hard_delete(self):
        """Physical delete"""
        super().delete()

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=["is_deleted"])
