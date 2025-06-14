from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import League, Round
from .managers import BetRoundManager, BetLeagueManager
from .utils import generate_unique_code

class AbstractBetModel(BaseModel):
    operation_code = models.CharField(max_length=20, null=True, blank=True)
    winner_first = models.BooleanField(default=False)
    winner_second = models.BooleanField(default=False)
    winner_third = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __save__(self, *args, **kwargs):
        if not self.operation_code:
            self.operation_code = generate_unique_code(self.__class__)
        super().save(*args, **kwargs)


class BetLeague(AbstractBetModel):
    user = models.ForeignKey(AppUser, related_name='bet_leagues', on_delete=models.CASCADE)
    league = models.ForeignKey(League, related_name='bet_leagues', on_delete=models.CASCADE)
    is_last_visited_league = models.BooleanField(default=False)

    objects = BetLeagueManager()

    def __str__(self):
        return f'{self.user.username} - {self.league.name}'
    
    def get_user_username(self):
        return self.user.username
    
    def get_user_profile_image(self):
        return self.user.profile_image.url
    
    def get_league_id(self):
        return self.league.id
    

class BetRound(AbstractBetModel):
    round = models.ForeignKey(Round, related_name='bet_rounds', on_delete=models.CASCADE)
    bet_league = models.ForeignKey(
        BetLeague, related_name='bet_rounds', on_delete=models.CASCADE, null=True, blank=True
    )

    objects = BetRoundManager()

    @property
    def points(self):
        if self.round.is_general_round:
            if self.bet_league:
                match_points = BetRound.objects.filter(
                    state=True,
                    bet_league__user=self.bet_league.user,
                    round__league=self.round.league,
                    round__is_general_round=False
                ).aggregate(total_points=models.Sum(
                    'match_results__points'
                ))['total_points'] or 0
            else:
                match_points = 0
        else:
            match_points = self.match_results.aggregate(
                total_points=models.Sum('points')
            )['total_points'] or 0

        return match_points
    
    def get_user(self):
        return self.bet_league.user

    def __str__(self):
        bet_league_user_username = self.bet_league.get_user_username() if self.bet_league else '-'
        return f'{bet_league_user_username} - {self.round.name}'
