from rest_framework import serializers
from .models import League, Round, Team

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        exclude = ('state', 'creation_date', 'updating_date')


class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        exclude = ('state', 'creation_date', 'updating_date')

    league = LeagueSerializer()


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        exclude = ('state', 'creation_date', 'updating_date')

    league = LeagueSerializer()