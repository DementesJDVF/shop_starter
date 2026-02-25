from django.db import models


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        return self.update(is_deleted=True)

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return self.update(is_deleted=False)

    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)