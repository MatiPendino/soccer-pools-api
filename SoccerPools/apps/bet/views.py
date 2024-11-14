from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League
from apps.match.models import Match, MatchResult
from apps.app_user.models import AppUser
from .serializers import BetSerializer, BetCreateSerializer
from .models import Bet

class LastFourWinnersView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = BetSerializer

    def get_queryset(self):
        winner_bets = Bet.objects.filter(winner=True).order_by('-updating_date')[:4]
        return winner_bets


class BetCreateApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = BetCreateSerializer(data=request.data)

        if serializer.is_valid():
            matches = Match.objects.filter(round=serializer.validated_data['round'])
            with transaction.atomic():
                bet = serializer.save()
                match_results = [MatchResult(match=soccer_match, bet=bet) for soccer_match in matches]
                MatchResult.objects.bulk_create(match_results)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeagueBetsMatchResultsCreateApiView(APIView):
    '''
        Creates Bet and MatchResult instances for the League selected by the user

        Payload:
        league_id -> Integer
        user_id -> Integer

        Response:
        league (String): Name of the league.
        user (String): Username of the user.
        bets (List): List of dictionaries containing `bet_id` and `round_id` for each created Bet.
    '''
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        league = get_object_or_404(League, slug=request.data['league_slug'])
        user = request.user
        rounds = Round.objects.filter(league=league)

        with transaction.atomic():
            # Creates bets for all the league rounds
            bets = [Bet(round=league_round, user=user) for league_round in rounds]
            Bet.objects.bulk_create(bets)

            # Creates match results for all the matches in all the bets
            for bet in bets:
                matches = Match.objects.filter(round=bet.round)
                match_results = [MatchResult(match=soccer_match, bet=bet) for soccer_match in matches]
                MatchResult.objects.bulk_create(match_results)

        response_data = {
            'league': league.name,
            'user': user.username,
            'bets': [
                {'bet_id': bet.id, 'round_id': bet.round.id} for bet in bets
            ]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

