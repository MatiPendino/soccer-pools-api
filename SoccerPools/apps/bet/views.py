from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League
from apps.match.models import Match, MatchResult
from apps.app_user.models import AppUser
from apps.tournament.models import TournamentUser
from .serializers import BetSerializer, BetCreateSerializer
from .models import Bet

class BetResultsApiView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BetSerializer

    def get_queryset(self,):
        round_slug = self.kwargs.get('round_slug')
        tournament_id = self.kwargs.get('tournament_id')

        bets = Bet.objects.filter(
            round__slug=round_slug, 
            state=True
        ).annotate(
            matches_points=Sum('match_result__points')
        ).order_by('-matches_points')

        if tournament_id != 0:
            tournament_users = TournamentUser.objects.filter(
                tournament__id=tournament_id,
                tournament_user_state=TournamentUser.ACCEPTED
            )
            users = [tournament_user.user for tournament_user in tournament_users]

            bets = bets.filter(user__in=users)

        return bets


class LeagueBetsMatchResultsCreateApiView(APIView):
    """
        Creates Bet and MatchResult instances for the League selected by the user

        Payload:
        league_slug -> Slug

        Response:
        league (String): Name of the league.
        user (String): Username of the user.
        bets (List): List of dictionaries containing `bet_id` and `round_id` for each created Bet.
    """
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        league = get_object_or_404(League, slug=request.data['league_slug'])
        user = request.user
        rounds = Round.objects.filter(league=league, state=True)

        with transaction.atomic():
            # Creates bets for all the league rounds
            bets = [Bet(round=league_round, user=user) for league_round in rounds]
            Bet.objects.bulk_create(bets)

            # Creates match results for all the matches in all the bets
            for bet in bets:
                matches = Match.objects.filter(round=bet.round, state=True)
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

