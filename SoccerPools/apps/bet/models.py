from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import League, Round
from .managers import BetRoundManager

class BetRound(BaseModel):
    user = models.ForeignKey(AppUser, related_name='bet_rounds', on_delete=models.CASCADE)
    operation_code = models.CharField(max_length=20, null=True, blank=True)
    round = models.ForeignKey(Round, related_name='bet_rounds', on_delete=models.CASCADE)
    winner = models.BooleanField(default=False)

    objects = BetRoundManager()

    @property
    def points(self):
        if self.round.is_general_round:
            match_points = BetRound.objects.filter(
                state=True,
                user=self.user,
                round__league=self.round.league,
                round__is_general_round=False
            ).aggregate(total_points=models.Sum(
                'match_results__points'
            ))['total_points'] or 0
        else:
            match_points = self.match_results.aggregate(
                total_points=models.Sum('points')
            )['total_points'] or 0

        return match_points

    def __str__(self):
        return f'{self.user} - {self.round.name}'
