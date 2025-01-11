from rest_framework import serializers
from .models import League, Round, Team

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ('id', 'name', 'slug', 'logo')


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
        fields = ('name', 'badge', 'slug')
