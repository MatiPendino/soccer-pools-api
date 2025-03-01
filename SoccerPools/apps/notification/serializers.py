from rest_framework import serializers
from apps.app_user.serializers import UserSerializer
from .models import FCMToken

class FCMTokenSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = FCMToken
        fields = ('token_id', 'user', 'device_id', 'leagues')