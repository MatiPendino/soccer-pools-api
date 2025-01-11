from rest_framework import serializers
from apps.league.serializers import RoundSerializer, TeamSerializer
from .models import Match, MatchResult


class MatchSerializer(serializers.ModelSerializer):
    team_1 = TeamSerializer(read_only=True)
    team_2 = TeamSerializer(read_only=True)
    round = RoundSerializer(read_only=True)
    class Meta:
        model = Match
        fields = ('id', 'team_1', 'team_2', 'round', 'start_date', 'match_state')

class MatchResultSerializer(serializers.ModelSerializer):
    match = MatchSerializer(read_only=True)
    class Meta:
        model = MatchResult
        fields = ('id', 'goals_team_1', 'goals_team_2', 'match')