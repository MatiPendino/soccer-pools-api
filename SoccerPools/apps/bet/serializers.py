from rest_framework import serializers
from .models import BetRound

class BetRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetRound
        fields = ('id', 'round', 'operation_code')

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.bet_league.get_user_username() if instance.bet_league else '',
            'profile_image': instance.bet_league.get_user_profile_image() if instance.bet_league else '',
            'points': instance.points,
            'operation_code': instance.operation_code,
            'round_id': instance.round.id
        }
    

class BetRoundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BetRound
        fields = ('user', 'round')