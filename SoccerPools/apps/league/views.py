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
        rounds = Round.objects.filter(
            league__id=self.kwargs['pk'], 
            state=True
        ).order_by('number_round')
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