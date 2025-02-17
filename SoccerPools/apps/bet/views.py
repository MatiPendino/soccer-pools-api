from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League
from apps.match.models import Match, MatchResult
from apps.app_user.models import AppUser
from apps.tournament.models import TournamentUser
from .serializers import BetRoundSerializer, BetRoundCreateSerializer
from .models import BetRound

class BetRoundResultsApiView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BetRoundSerializer

    def get_queryset(self,):
        round_slug = self.kwargs.get('round_slug')
        tournament_id = self.kwargs.get('tournament_id')
        bet_rounds = BetRound.objects.with_matches_points(round_slug=round_slug)

        if tournament_id != 0:
            tournament_users = TournamentUser.objects.filter(
                tournament__id=tournament_id,
                tournament_user_state=TournamentUser.ACCEPTED
            )
            users = [tournament_user.user for tournament_user in tournament_users]

            bet_rounds = bet_rounds.filter(user__in=users)

        return bet_rounds


class LeagueBetRoundsMatchResultsCreateApiView(APIView):
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
            bet_rounds = [BetRound(round=league_round, user=user) for league_round in rounds]
            BetRound.objects.bulk_create(bet_rounds)

            # Creates match results for all the matches in all the bets
            for bet_round in bet_rounds:
                matches = Match.objects.filter(round=bet_round.round, state=True)
                match_results = [MatchResult(match=soccer_match, bet_round=bet_round) for soccer_match in matches]
                MatchResult.objects.bulk_create(match_results)

        response_data = {
            'league': league.name,
            'user': user.username,
            'bets': [
                {'bet_id': bet_round.id, 'round_id': bet_round.round.id} for bet_round in bet_rounds
            ]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

