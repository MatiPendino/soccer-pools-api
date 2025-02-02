from django.shortcuts import render
from rest_framework import generics
from .serializers import LeagueSerializer, RoundSerializer, TeamSerializer
from .models import League, Round, Team

class LeagueListApiView(generics.ListAPIView):
    serializer_class = LeagueSerializer
    queryset = League.objects.filter(state=True)
    

class LeagueRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = LeagueSerializer
    queryset = League.objects.filter(state=True)


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