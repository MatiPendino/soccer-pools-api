from django.test import TestCase
from apps.league.models import Round
from apps.league.factories import RoundFactory, LeagueFactory

class UpdateRoundWinnersPrizesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory()
        self.round = RoundFactory(round_state=Round.FINALIZED_ROUND, league=self.league)
        
