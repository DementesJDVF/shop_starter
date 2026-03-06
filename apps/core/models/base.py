from django.db import models
from .managers import SoftDeleteManager, AllObjectsManager


class BaseModel(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft delete"""
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])

    def hard_delete(self, using=None, keep_parents=False):
        """Physical delete"""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=["is_deleted"])
