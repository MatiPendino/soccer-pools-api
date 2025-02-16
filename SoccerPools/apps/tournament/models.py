from django.db import models
from apps.app_user.models import AppUser
from apps.base.models import BaseModel
from apps.league.models import League

class Tournament(BaseModel):
    LOGO_FOLDER_NAME = 'tournament'
    LOGO_DEFAULT_FILE_NAME = 'default-tournament-logo.png'
    
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(upload_to=LOGO_FOLDER_NAME, default=LOGO_DEFAULT_FILE_NAME, blank=True, null=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    admin_tournament = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def n_participants(self):
        n_tournament_users = TournamentUser.objects.filter(
            state=True,
            tournament=self,
            tournament_user_state=TournamentUser.ACCEPTED
        ).count()
        return n_tournament_users

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