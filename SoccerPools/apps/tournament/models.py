from django.db import models
from apps.app_user.models import AppUser
from apps.base.models import BaseModel
from apps.league.models import League

class Tournament(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to='tournament', default='default-tournament-logo.png')
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    admin_tournament = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class TournamentUser(BaseModel):
    NOT_SENT = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3
    TOURNAMENT_USER_STATES = (
        (NOT_SENT, 'NOT SENT'),
        (PENDING , 'PENDING'),
        (ACCEPTED , 'ACCEPTED'),
        (REJECTED , 'REJECTED')
    )

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    tournament_user_state = models.IntegerField(choices=TOURNAMENT_USER_STATES, default=NOT_SENT)

    def __str__(self):
        return f'{self.tournament.name} - {self.user.username}'