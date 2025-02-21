from rest_framework import serializers
from apps.bet.models import BetLeague
from .models import League, Round, Team

class LeagueSerializer(serializers.ModelSerializer):
    is_user_joined = serializers.SerializerMethodField()

    class Meta:
        model = League
        fields = ('id', 'name', 'slug', 'logo', 'is_user_joined')

    def get_is_user_joined(self, obj):
        """Check if the current user is in a BetLeague with this league"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return BetLeague.objects.filter(state=True, user=request.user, league=obj).exists()
        return False


class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = (
            'id', 'name', 'slug', 'number_round', 'start_date', 'end_date', 'round_state',
            'league'
        )

    league = LeagueSerializer()


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('name', 'badge', 'slug', 'acronym')
