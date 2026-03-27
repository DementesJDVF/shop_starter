from rest_framework import serializers
from users.models import User

class UserSerializers(serializers.ModelSerializer):
    class meta: 
        model = User 
        fields = [
            'username'
            'first_name'
            'last_name'
            'email'
            'id'
            'role'
            'status'
        ]
        