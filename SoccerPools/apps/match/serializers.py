from rest_framework import serializers
from .models import MatchResult

class MatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchResult
        fields = ('goals_team_1', 'goals_team_2', 'match')

    def to_representation(self, instance):
        return {
            'goals_team_1': instance.goals_team_1,
            'goals_team_2': instance.goals_team_2,
            'team_1': instance.match.get_team_acronyms()[0],
            'team_2': instance.match.get_team_acronyms()[1],
            'badge_team_1': instance.match.get_team_badges()[0],
            'badge_team_2': instance.match.get_team_badges()[1]
        }