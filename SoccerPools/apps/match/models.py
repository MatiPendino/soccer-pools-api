from django.db import models
from apps.base.models import BaseModel
from apps.league.models import Team, Round
from apps.bet.models import Bet


class Match(BaseModel):
    team_1 = models.ForeignKey(Team, related_name='team_1', on_delete=models.CASCADE)
    team_2 = models.ForeignKey(Team, related_name='team_2', on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    start_date = models.DateTimeField('Start date of the match', blank=True, null=True)

    def __str__(self):
        return f'{self.team_1.name} vs {self.team_2.name} - {self.round.name}'
    
    class Meta:
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'

    def get_team_names(self):
        return [self.team_1.name, self.team_2.name]



class MatchResult(BaseModel):
    goals_team_1 = models.PositiveSmallIntegerField(default=0)
    goals_team_2 = models.PositiveSmallIntegerField(default=0)
    original_result = models.BooleanField('Original result', default=False)
    bet = models.ForeignKey(Bet, on_delete=models.SET_NULL, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)

    def __str__(self):
        nteam_1, nteam_2 = self.match.get_team_names()
        return f'{nteam_1} {self.goals_team_1} - {self.goals_team_2} {nteam_2}'
    
    class Meta:
        verbose_name = 'Match Result'
        verbose_name_plural = 'Matches results'