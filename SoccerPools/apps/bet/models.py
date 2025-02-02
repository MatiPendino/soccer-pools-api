from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import Round
from .managers import BetManager

class Bet(BaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    operation_code = models.CharField(max_length=20, null=True, blank=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    winner = models.BooleanField(default=False)

    objects = BetManager()

    @property
    def points(self):
        if self.round.is_general_round:
            match_points = Bet.objects.filter(
                state=True,
                user=self.user,
                round__league=self.round.league,
                round__is_general_round=False
            ).aggregate(total_points=models.Sum(
                'match_result__points'
            ))['total_points'] or 0
        else:
            match_points = self.match_result.aggregate(
                total_points=models.Sum('points')
            )['total_points'] or 0

        return match_points

    def __str__(self):
        return f'{self.user} - {self.round.name}'
