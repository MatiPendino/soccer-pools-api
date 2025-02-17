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