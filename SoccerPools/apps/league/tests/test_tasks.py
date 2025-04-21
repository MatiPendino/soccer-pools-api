from django.test import TestCase
from django.utils.timezone import now, timedelta
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.league.models import Round
from apps.match.models import Match
from apps.bet.models import BetRound
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

        self.coins = 3000
        self.user_1 = AppUserFactory(coins=self.coins)
        self.user_2 = AppUserFactory(coins=self.coins)
        self.user_3 = AppUserFactory(coins=self.coins)
        self.user_4 = AppUserFactory(coins=self.coins)
        self.bet_league_1 = BetLeagueFactory(user=self.user_1, league=self.league)
        self.bet_round_1 = BetRoundFactory(bet_league=self.bet_league_1, round=self.round_2)
        self.bet_league_2 = BetLeagueFactory(user=self.user_2, league=self.league)
        self.bet_round_2 = BetRoundFactory(bet_league=self.bet_league_2, round=self.round_2)
        self.bet_league_3 = BetLeagueFactory(user=self.user_3, league=self.league)
        self.bet_round_3 = BetRoundFactory(bet_league=self.bet_league_3, round=self.round_2)
        self.bet_league_4 = BetLeagueFactory(user=self.user_4, league=self.league)
        self.bet_round_4 = BetRoundFactory(bet_league=self.bet_league_4, round=self.round_2)

        self.match_result_1 = MatchResultFactory(match=self.match_2, bet_round=self.bet_round_1, points=3)
        self.match_result_2 = MatchResultFactory(match=self.match_3, bet_round=self.bet_round_2, points=2)
        self.match_result_3 = MatchResultFactory(match=self.match_3, bet_round=self.bet_round_3, points=1)
        self.match_result_4 = MatchResultFactory(match=self.match_3, bet_round=self.bet_round_4, points=0)

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

        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()
        self.user_3.refresh_from_db()
        self.user_4.refresh_from_db()
        self.bet_round_1.refresh_from_db()
        self.bet_round_2.refresh_from_db()
        self.bet_round_3.refresh_from_db()
        self.bet_round_4.refresh_from_db()

        self.assertTrue(self.bet_round_1.winner_first)
        self.assertTrue(self.bet_round_2.winner_second)
        self.assertTrue(self.bet_round_3.winner_third)
        self.assertFalse(self.bet_round_4.winner_first)
        self.assertFalse(self.bet_round_4.winner_second)
        self.assertFalse(self.bet_round_4.winner_third)

        total_coins_user_1 = self.coins + BetRound.objects.count() * Round.COINS_FIRST_PRIZE_MULT
        total_coins_user_2 = self.coins + BetRound.objects.count() * Round.COINS_SECOND_PRIZE_MULT
        total_coins_user_3 = self.coins + BetRound.objects.count() * Round.COINS_THIRD_PRIZE_MULT
        self.assertEqual(self.user_1.coins, total_coins_user_1)
        self.assertEqual(self.user_2.coins, total_coins_user_2)
        self.assertEqual(self.user_3.coins, total_coins_user_3)
        self.assertEqual(self.user_4.coins, self.coins)