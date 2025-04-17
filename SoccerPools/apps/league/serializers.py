from rest_framework import serializers
from apps.bet.models import BetLeague, BetRound
from .models import League, Round, Team

class LeagueSerializer(serializers.ModelSerializer):
    is_user_joined = serializers.SerializerMethodField()

    class Meta:
        model = League
        fields = (
            'id', 'name', 'slug', 'logo', 'continent', 'is_user_joined', 'coins_cost', 'coins_prizes'
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not data['logo']:
            data['logo'] = instance.logo_url

        return data

    def get_is_user_joined(self, obj):
        """Check if the current user is in a BetLeague with this league"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return BetLeague.objects.filter(state=True, user=request.user, league=obj).exists()
        return False


class RoundSerializer(serializers.ModelSerializer):
    has_bet_round = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = (
            'id', 'name', 'slug', 'number_round', 'start_date', 'end_date', 'round_state',
            'league', 'has_bet_round', 'coins_prizes'
        )

    league = LeagueSerializer()

    def get_has_bet_round(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return BetRound.objects.filter(
                state=True,
                bet_league__user=request.user,
                round=obj
            ).exists()
        return False


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('name', 'badge', 'slug', 'acronym')

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if not data['badge']:
            data['badge'] = instance.badge_url

        return data
