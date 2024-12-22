from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import Round


class Bet(BaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    operation_code = models.CharField(max_length=20, null=True, blank=True)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    points = models.PositiveSmallIntegerField(default=0)
    winner = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.round.name}'
