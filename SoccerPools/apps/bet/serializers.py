from rest_framework import serializers
from .models import Bet

class BetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ('user', 'round', 'points', 'winner')

    def to_representation(self, instance):
        return {
            'username': instance.user.username,
            'profile_image': instance.user.profile_image.url,
            'round': instance.round.name,
            'league': instance.round.league.name,
            'winner': instance.winner,
            'points': instance.points,
            'n_players': instance.round.get_number_bets(),
            'pool': instance.round.pool,
        }