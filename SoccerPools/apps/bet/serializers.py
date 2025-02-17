from rest_framework import serializers
from .models import BetRound

class BetRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetRound
        fields = ('id', 'user', 'round', 'operation_code')

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.user.username,
            'profile_image': instance.user.profile_image.url,
            'points': instance.points,
            'operation_code': instance.operation_code,
            'round_id': instance.round.id
        }
    

class BetRoundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetRound
        fields = ('user', 'round')