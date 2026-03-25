import uuid

from django.db import models


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(
        "vendors.VendorProfile",
        on_delete=models.CASCADE,
        related_name="locations",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)

    description =models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "geo_location"

    def __str__(self):
        return f"{self.vendor} @ ({self.latitude}, {self.longitude})"
