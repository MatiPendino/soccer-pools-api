from django.db.models import (
    Sum, IntegerField, F, Q, ExpressionWrapper, Value, Manager
)
from django.db.models.functions import Coalesce

class BetRoundManager(Manager):
    def with_matches_points(self, round_slug):
        """
            Filters the bet rounds based on the received round_slug, and makes an annotation 
            for the bet round points

            Returns the queryset ordered by matches_points desc
        """
        return self.filter(
            round__slug=round_slug, 
            state=True
        ).annotate(
            matches_points=ExpressionWrapper(
                # If round.is_general_round == True, sum points from all bets in the same league
                Coalesce(
                    Sum(
                        'user__bet_rounds__match_results__points',
                        filter=(
                            Q(round__is_general_round=True) &
                            Q(user__bet_rounds__state=True) &
                            Q(user__bet_rounds__round__league=F('round__league'))
                        )
                    ), Value(0),
                    output_field=IntegerField()
                ) + 
                # Otherwise, sum points from match results directly related to the instance
                Coalesce(
                    Sum(
                        'match_results__points',
                        filter=(
                            Q(round__is_general_round=False) 
                        )
                    ), Value(0),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            )
        ).order_by('-matches_points')
    

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