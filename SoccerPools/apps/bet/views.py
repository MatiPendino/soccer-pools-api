from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League
from apps.match.models import Match, MatchResult
from apps.tournament.models import TournamentUser
from .serializers import BetRoundSerializer
from .models import BetRound, BetLeague
from .utils import generate_response_data

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
        Creates BetLeague, BetRound and MatchResult instances for the League selected by the user
        If there is an existing BetLeague, returns it without new creations

        Payload:
        league_slug -> Slug

        Response:
        league (String): Name of the league.
        user (String): Username of the user.
        bet_league_id (Integer): Id of the new BetLeague instance.
        bet_rounds (List): List of dictionaries containing `bet_round_id` and `round_id` for each created Bet.
    """
    permissions_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        league = get_object_or_404(League, slug=request.data['league_slug'])
        user = request.user
        rounds = Round.objects.filter(league=league, state=True)

        # Deactivate if there is another bet_league instance with last_visited in True
        BetLeague.objects.deactivate_last_visited_bet_league(user)

        # If there is already a BetLeague instance for this league and user, set 
        # is_last_visited_league to True and DO NOT CREATE ANY NEW BetLeague, BetRound or MatchResult 
        existing_user_bet_league = BetLeague.objects.filter(state=True, league=league, user=user)
        if existing_user_bet_league.exists():
            existing_user_bet_league = existing_user_bet_league.first()
            existing_user_bet_league.is_last_visited_league = True
            existing_user_bet_league.save()

            bet_rounds = BetRound.objects.filter(
                state=True,
                user=user,
                round__league=league
            )
            response_data = generate_response_data(
                league_name=league.name,
                username=user.username,
                bet_league_id=existing_user_bet_league.id,
                bet_rounds=bet_rounds
            )

            return Response(response_data, status=status.HTTP_200_OK)


        with transaction.atomic():
            # Create bet_league
            new_bet_league = BetLeague.objects.create(
                user=user, 
                league=league, 
                is_last_visited_league=True
            )

            # Create bet rounds for all the league rounds
            bet_rounds = [
                BetRound(round=league_round, user=user, bet_league=new_bet_league) 
                for league_round in rounds
            ]
            BetRound.objects.bulk_create(bet_rounds)

            # Create match results for all the matches in all the bets
            for bet_round in bet_rounds:
                matches = Match.objects.filter(round=bet_round.round, state=True)
                match_results = [MatchResult(match=soccer_match, bet_round=bet_round) for soccer_match in matches]
                MatchResult.objects.bulk_create(match_results)

        response_data = generate_response_data(
            league_name=league.name,
            username=user.username,
            bet_league_id=new_bet_league.id,
            bet_rounds=bet_rounds
        )

        return Response(response_data, status=status.HTTP_201_CREATED)

