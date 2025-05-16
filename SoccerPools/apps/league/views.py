from rest_framework import generics
from .serializers import LeagueSerializer, RoundSerializer, TeamSerializer
from .models import League, Round, Team

class LeagueListApiView(generics.ListAPIView):
    serializer_class = LeagueSerializer

    def get_queryset(self):
        continent = self.request.query_params.get('continent')
        if continent != 'undefined':
            continent = int(continent)
        leagues = League.objects.filter(
            state=True,
            league_state__in=[League.NOT_STARTED_LEAGUE, League.PENDING_LEAGUE]
        ).order_by('name')
        if continent in [
            League.AMERICAS, League.AFRICA, League.EUROPE, League.ASIA, League.OCEANIA, 
            League.TOURNAMENTS
        ]:
            leagues = leagues.filter(continent=continent)

        return leagues

    def get_serializer_context(self):
        """Pass request context so we can access the user in the serializer."""
        return {'request': self.request}
    

class LeagueRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = LeagueSerializer
    queryset = League.objects.filter(state=True)

    def get_serializer_context(self):
        """Pass request context so we can access the user in the serializer."""
        return {'request': self.request}


class RoundListApiView(generics.ListAPIView):
    serializer_class = RoundSerializer

    def get_queryset(self):
        """
            Returns all the rounds for the specified league_id
            If receive the not_general_round query param, exclude General Round
        """
        league_id = self.kwargs.get('pk')
        not_general_round = self.request.query_params.get('not_general_round')
        rounds = Round.objects.filter(
            league__id=league_id, 
            state=True
        ).order_by('number_round')

        if not_general_round != 'undefined':
            rounds = rounds.filter(
                is_general_round=False
            )

        return rounds


class RoundRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = RoundSerializer
    queryset = Round.objects.filter(state=True)


class TeamListApiView(generics.ListAPIView):
    serializer_class = TeamSerializer
    queryset = Team.objects.filter(state=True)


class TeamRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = TeamSerializer
    queryset = Team.objects.filter(state=True)