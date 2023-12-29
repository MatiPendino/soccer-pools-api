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


class NextRoundsListApiView(generics.ListAPIView):
    serializer_class = RoundSerializer
    queryset = Round.objects.filter(state=True, round_state=Round.NOT_STARTED_ROUND)

class CurrentRoundsListApiView(generics.ListAPIView):
    serializer_class = RoundSerializer
    queryset = Round.objects.filter(state=True, round_state=Round.PENDING_ROUND)

class ExpiredRoundsListApiView(generics.ListAPIView):
    serializer_class = RoundSerializer
    queryset = Round.objects.filter(state=True, round_state=Round.FINALIZED_ROUND)


class RoundRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = RoundSerializer
    queryset = Round.objects.filter(state=True)


class TeamListApiView(generics.ListAPIView):
    serializer_class = TeamSerializer
    queryset = Team.objects.filter(state=True)


class TeamRetrieveApiView(generics.RetrieveAPIView):
    serializer_class = TeamSerializer
    queryset = Team.objects.filter(state=True)