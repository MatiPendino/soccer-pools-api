from rest_framework import serializers
from apps.app_user.serializers import UserSerializer
from apps.league.serializers import LeagueSerializer
from .models import Tournament, TournamentUser

class TournamentSerializer(serializers.ModelSerializer):
    is_current_user_admin = serializers.SerializerMethodField()
    current_user_state = serializers.SerializerMethodField()
    participants_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Tournament
        fields = (
            'id', 'name', 'description', 'logo', 'league', 'admin_tournament', 'n_participants',
            'is_current_user_admin', 'tournament_type', 'current_user_state', 
            'participants_count',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['admin_tournament'] = UserSerializer(instance.admin_tournament).data
        data['league'] = LeagueSerializer(instance.league).data

        return data
    
    def get_is_current_user_admin(self, obj):
        """Check if the current user is the tournament admin"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.admin_tournament:
            return obj.admin_tournament.id == request.user.id
        return False

    def get_current_user_state(self, obj):
        """Return the TournamentUser state for the current user or null if not a member"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                tournament_user = TournamentUser.objects.get(
                    tournament=obj, user=request.user, state=True
                )
                return tournament_user.tournament_user_state
            except TournamentUser.DoesNotExist:
                return None
        return None


class TournamentUserSerializer(serializers.ModelSerializer):
    tournament = TournamentSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = TournamentUser
        fields = ('id', 'tournament', 'user', 'tournament_user_state')