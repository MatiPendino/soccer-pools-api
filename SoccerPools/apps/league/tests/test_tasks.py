from django.test import TestCase
from django.utils.timezone import now, timedelta
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.match.factories import MatchFactory
from apps.league.models import Round
from apps.match.models import Match
from apps.league.tasks import check_upcoming_rounds, finalize_pending_rounds


class UpcomingRoundsTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory(name='Upcoming Rounds Test')
        self.round_1 = RoundFactory(league=self.league, start_date=now()+timedelta(minutes=10))
        self.round_2 = RoundFactory(league=self.league, start_date=now()+timedelta(minutes=30))
        self.round_3 = RoundFactory(league=self.league, start_date=now()+timedelta(minutes=20))
        self.round_4 = RoundFactory(league=self.league, start_date=now()-timedelta(minutes=1))

    def test_upcoming_rounds(self):
        """Test that rounds change its state to pending"""
        check_upcoming_rounds()

        self.round_1.refresh_from_db()
        self.round_2.refresh_from_db()
        self.round_3.refresh_from_db()
        self.round_4.refresh_from_db()

        self.assertEqual(self.round_1.round_state, Round.PENDING_ROUND)
        self.assertEqual(self.round_2.round_state, Round.NOT_STARTED_ROUND)
        self.assertEqual(self.round_3.round_state, Round.PENDING_ROUND)
        self.assertEqual(self.round_4.round_state, Round.NOT_STARTED_ROUND)


class FinalizePendingRoundsTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory(slug='FinalizePendingTest')
        self.round_1 = RoundFactory(league=self.league, round_state=Round.NOT_STARTED_ROUND)
        self.round_2 = RoundFactory(league=self.league, round_state=Round.PENDING_ROUND)
        self.round_3 = RoundFactory(league=self.league, round_state=Round.PENDING_ROUND)
        self.round_4 = RoundFactory(league=self.league, round_state=Round.FINALIZED_ROUND)
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.match_1 = MatchFactory(
            round=self.round_1,
            team_1=self.team_1, 
            team_2=self.team_2,
            match_state=Match.FINALIZED_MATCH
        )
        self.match_2 = MatchFactory(
            round=self.round_2,
            team_1=self.team_1, 
            team_2=self.team_3,
            match_state=Match.FINALIZED_MATCH
        )
        self.match_3 = MatchFactory(
            round=self.round_2,
            team_1=self.team_2, 
            team_2=self.team_4,
            match_state=Match.FINALIZED_MATCH
        )
        self.match_4 = MatchFactory(
            round=self.round_3,
            team_1=self.team_1, 
            team_2=self.team_4,
            match_state=Match.FINALIZED_MATCH
        )
        self.match_5 = MatchFactory(
            round=self.round_3,
            team_1=self.team_2, 
            team_2=self.team_3,
            match_state=Match.PENDING_MATCH
        )
        self.match_6 = MatchFactory(
            round=self.round_4,
            team_1=self.team_3, 
            team_2=self.team_4,
            match_state=Match.FINALIZED_MATCH
        )

    def test_finalize_pending_rounds(self):
        """
            Test that all PENDING Rounds with all their Matches FINALIZED 
            update round_state to FINALIZED
        """
        finalize_pending_rounds()

        self.round_1.refresh_from_db()
        self.round_2.refresh_from_db()
        self.round_3.refresh_from_db()
        self.round_4.refresh_from_db()

        self.assertEqual(self.round_1.round_state, Round.NOT_STARTED_ROUND)
        self.assertEqual(self.round_2.round_state, Round.FINALIZED_ROUND)
        self.assertEqual(self.round_3.round_state, Round.PENDING_ROUND)
        self.assertEqual(self.round_4.round_state, Round.FINALIZED_ROUND)