from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import Round
from apps.match.models import MatchResult


class Bet(BaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    operation_code = models.CharField(max_length=20, null=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    points = models.PositiveSmallIntegerField(default=0)
    match_results = models.ManyToManyField(MatchResult)
    winner = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.operation_code} - {self.user} - {self.round.name}'
