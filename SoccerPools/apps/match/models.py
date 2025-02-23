from django.db import models
from apps.base.models import BaseModel
from apps.league.models import Team, Round
from apps.bet.models import BetRound


class Match(BaseModel):
    NOT_STARTED_MATCH = 0
    PENDING_MATCH = 1
    FINALIZED_MATCH = 2
    CANCELLED_MATCH = 3
    STATE_CODES = (
        (NOT_STARTED_MATCH, 'Not started'),
        (PENDING_MATCH, 'Pending'),
        (FINALIZED_MATCH, 'Finalized'),
        (CANCELLED_MATCH, 'Cancelled')
    )

    team_1 = models.ForeignKey(Team, related_name='team_1', on_delete=models.CASCADE)
    team_2 = models.ForeignKey(Team, related_name='team_2', on_delete=models.CASCADE)
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    start_date = models.DateTimeField('Start date of the match', blank=True, null=True)
    match_state = models.PositiveSmallIntegerField('State of the match', default=0, choices=STATE_CODES)
    api_match_id = models.PositiveIntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return f'{self.team_1.name} vs {self.team_2.name} - {self.round.name}'
    
    class Meta:
        verbose_name = 'Match'
        verbose_name_plural = 'Matches'

    def get_team_names(self):
        return [self.team_1.name, self.team_2.name]
    
    def get_team_acronyms(self):
        return [self.team_1.acronym, self.team_2.acronym]

    def get_team_badges(self):
        return [self.team_1.badge.url, self.team_2.badge.url]


class MatchResult(BaseModel):
    goals_team_1 = models.PositiveSmallIntegerField(default=0)
    goals_team_2 = models.PositiveSmallIntegerField(default=0)
    original_result = models.BooleanField('Original result', default=False)
    bet_round = models.ForeignKey(BetRound, related_name='match_results', on_delete=models.SET_NULL, null=True, blank=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    points = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        nteam_1, nteam_2 = self.match.get_team_names()
        return f'{nteam_1} {self.goals_team_1} - {self.goals_team_2} {nteam_2}'
    
    class Meta:
        verbose_name = 'Match Result'
        verbose_name_plural = 'Matches results'