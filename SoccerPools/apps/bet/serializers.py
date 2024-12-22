from rest_framework import serializers
from .models import Bet

class BetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ('id', 'user', 'round', 'points', 'operation_code')

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.user.username,
            'profile_image': instance.user.profile_image.url,
            'points': instance.points,
            'operation_code': instance.operation_code,
            'round_id': instance.round.id
        }
    

class BetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ('user', 'round')