from rest_framework import serializers
from .models import Bet

class BetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ('user', 'round', 'points', 'winner')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['username'] = instance.user.username
        representation['profile_image'] = instance.user.profile_image.url
        representation['round'] = instance.round.name
        representation['league'] = instance.round.league.name
        representation['n_players'] = instance.round.get_number_bets()
        representation['pool'] = instance.round.pool
        
        return representation
    

class BetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        fields = ('user', 'round')