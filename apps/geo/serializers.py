from rest_framework import serializers
from apps.geo.models import Location
from apps.users.models import User
from apps.users.constants import UserRoles
class LocationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    #vendor = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=UserRoles.VENDOR))
    class Meta:
        model = Location
        fields = "__all__"