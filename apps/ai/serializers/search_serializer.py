from rest_framework import serializers


class UserLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class AISearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=400)
    user_location = UserLocationSerializer()


class AISearchResultItemSerializer(serializers.Serializer):
    product = serializers.CharField()
    vendor = serializers.CharField()
    distance = serializers.FloatField(allow_null=True)
    price = serializers.FloatField()


class AISearchResponseSerializer(serializers.Serializer):
    filters = serializers.DictField()
    results = AISearchResultItemSerializer(many=True)
