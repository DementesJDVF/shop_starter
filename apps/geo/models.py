from django.db import models
from apps.vendors.models import Vendor

class Location(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)