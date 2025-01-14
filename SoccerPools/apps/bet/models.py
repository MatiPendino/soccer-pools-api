from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import Round


class Bet(BaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    operation_code = models.CharField(max_length=20, null=True, blank=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    winner = models.BooleanField(default=False)

    @property
    def points(self):
        match_results = self.match_result.prefetch_related()
        match_points = sum([match_result.points for match_result in match_results])

        return match_points

    def __str__(self):
        return f'{self.user} - {self.round.name}'
