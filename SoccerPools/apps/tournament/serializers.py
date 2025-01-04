from rest_framework import serializers
from apps.app_user.serializers import UserSerializer
from .models import Tournament, TournamentUser

class TournamentSerializer(serializers.ModelSerializer):
    admin_tournament = UserSerializer(read_only=True)

    class Meta:
        model = Tournament
        fields = ('id', 'name', 'description', 'logo', 'league', 'admin_tournament')


class TournamentUserSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = TournamentUser
        fields = ('id', 'tournament', 'user', 'tournament_user_state')