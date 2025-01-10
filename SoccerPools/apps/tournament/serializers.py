from rest_framework import serializers
from apps.app_user.serializers import UserSerializer
from apps.league.serializers import LeagueSerializer
from .models import Tournament, TournamentUser

class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = ('id', 'name', 'description', 'logo', 'league', 'admin_tournament', 'n_participants')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['admin_tournament'] = UserSerializer(instance.admin_tournament).data
        data['league'] = LeagueSerializer(instance.league).data

        return data


class TournamentUserSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = TournamentUser
        fields = ('id', 'tournament', 'user', 'tournament_user_state')