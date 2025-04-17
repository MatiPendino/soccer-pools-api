from django.db.models import (
    Sum, IntegerField, F, Q, ExpressionWrapper, Value, Manager
)
from django.shortcuts import get_object_or_404
from django.db.models.functions import Coalesce
from apps.league.models import Round

class BetRoundManager(Manager):
    def with_matches_points(self, round_slug):
        """
            Filters the bet rounds based on the received round_slug, and makes an annotation 
            for the bet round points

            Returns the queryset ordered by matches_points desc
        """
        round = get_object_or_404(Round, slug=round_slug)
        bet_rounds = self.filter(
            round__slug=round_slug, 
            state=True
        )

        if round.is_general_round:
            bet_rounds = bet_rounds.annotate(
                matches_points=ExpressionWrapper(
                    Coalesce(
                        Sum(
                            'bet_league__bet_rounds__match_results__points',
                            filter=(
                                Q(round__is_general_round=True) &
                                Q(bet_league__bet_rounds__state=True) &
                                Q(bet_league__bet_rounds__round__league=F('round__league'))
                            )
                        ), Value(0),
                        output_field=IntegerField()
                    ), output_field=IntegerField()
                )
            )
        else:
            bet_rounds = bet_rounds.annotate(
                matches_points=ExpressionWrapper(
                    Coalesce(
                        Sum(
                            'match_results__points',
                            filter=(
                                Q(round__is_general_round=False) 
                            )
                        ), Value(0),
                        output_field=IntegerField()
                    ), output_field=IntegerField()
                )
            )

        return bet_rounds.order_by('-matches_points')
    

class BetLeagueManager(Manager):
    def get_last_visited_bet_league(self, user):
        bet_league = self.filter(
            user=user, 
            state=True,
            is_last_visited_league=True
        ).first()
        if not bet_league:
            bet_league = self.filter(
                user=user,
                state=True
            ).first()
            bet_league.is_last_visited_league = True
            bet_league.save()

        return bet_league
    
    def deactivate_last_visited_bet_league(self, user):
        bet_league_user_last_visited = self.filter(
            state=True,
            user=user,
            is_last_visited_league=True
        )
        if bet_league_user_last_visited.exists():
            bet_league_user_last_visited = bet_league_user_last_visited.first()
            bet_league_user_last_visited.is_last_visited_league = False
            bet_league_user_last_visited.save()