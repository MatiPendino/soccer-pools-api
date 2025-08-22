from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from django.core import mail
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.match.models import MatchResult, Match
from apps.match.factories import MatchResultFactory, MatchFactory
from apps.match.tasks import (
    check_upcoming_matches, finalize_matches, update_matches_start_date, check_suspended_matches
)

User = get_user_model()
class UpcomingMatchesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory()
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.round = RoundFactory(league=self.league)
        self.match_1 = MatchFactory(
            team_1=self.team_1, 
            team_2=self.team_2, 
            match_state=Match.NOT_STARTED_MATCH,
            round=self.round,
            start_date=now()+timedelta(minutes=15)
        )
        self.match_2 = MatchFactory(
            team_1=self.team_3, 
            team_2=self.team_4, 
            match_state=Match.NOT_STARTED_MATCH,
            round=self.round,
            start_date=now()+timedelta(minutes=25)
        )
        self.match_3 = MatchFactory(
            team_1=self.team_1, 
            team_2=self.team_4, 
            match_state=Match.PENDING_MATCH,
            round=self.round,
            start_date=now()+timedelta(minutes=10)
        )
        self.match_4 = MatchFactory(
            team_1=self.team_2, 
            team_2=self.team_3, 
            match_state=Match.NOT_STARTED_MATCH,
            round=self.round,
            start_date=now()+timedelta(seconds=30)
        )

    def test_update_matches_state(self):
        """Test that not started matches with start date within 20 minutes change its state"""
        check_upcoming_matches()
        self.match_1.refresh_from_db()
        self.match_2.refresh_from_db()
        self.match_3.refresh_from_db()
        self.match_4.refresh_from_db()
        self.assertEqual(self.match_1.match_state, Match.PENDING_MATCH)
        self.assertEqual(self.match_2.match_state, Match.NOT_STARTED_MATCH)
        self.assertEqual(self.match_3.match_state, Match.PENDING_MATCH)
        self.assertEqual(self.match_4.match_state, Match.PENDING_MATCH)


class FinalizeMatchesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory(name='Finalize Testing')
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.round = RoundFactory(league=self.league)
        self.match_1 = MatchFactory(
            team_1=self.team_1, 
            team_2=self.team_2, 
            match_state=Match.PENDING_MATCH,
            round=self.round,
        )
        self.match_2 = MatchFactory(
            team_1=self.team_3, 
            team_2=self.team_4, 
            match_state=Match.NOT_STARTED_MATCH,
            round=self.round,
        )

        self.user_1 = User.objects.create_user(
            username='mati1',
            email='mati1@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )
        self.user_2 = User.objects.create_user(
            username='mati2',
            email='mati2@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )

        self.bet_league_1 = BetLeagueFactory(league=self.league, user=self.user_1)
        self.bet_round_1 = BetRoundFactory(round=self.round)
        self.bet_league_2 = BetLeagueFactory(league=self.league, user=self.user_2)
        self.bet_round_2 = BetRoundFactory(round=self.round)
        self.match_result_1 = MatchResultFactory(
            goals_team_1=2, goals_team_2=1,
            bet_round=self.bet_round_1,
            match=self.match_1
        )
        self.match_result_2 = MatchResultFactory(
            goals_team_1=2, goals_team_2=1,
            bet_round=self.bet_round_1,
            match=self.match_2
        )
        self.match_result_3 = MatchResultFactory(
            goals_team_1=1, goals_team_2=0,
            bet_round=self.bet_round_2,
            match=self.match_1
        )
        self.match_result_4 = MatchResultFactory(
            goals_team_1=0, goals_team_2=0,
            bet_round=self.bet_round_2,
            match=self.match_2
        )
        self.match_result_5 = MatchResultFactory(
            goals_team_1=2, goals_team_2=None,
            bet_round=self.bet_round_2,
            match=self.match_2
        )

    @patch('apps.match.tasks.requests.get')
    def test_finalize_matches(self, mock_requests_get):
        """
        Test that finalize_matches correctly updates match states when API reports 
        finished matches
        """
        self.match_1.api_match_id = 423423 # Any number, it is a fake api called, doesnt matter
        self.match_2.api_match_id = 42342
        self.match_1.save()
        self.match_2.save()

        # Create a mock API response
        fake_api_response = """{
            "response": [{
                "goals": {"home": 2, "away": 1}, 
                "fixture": {"status": {"long": "Match Finished"}} 
            }]
        }"""

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get.return_value.text = fake_api_response
        mock_requests_get.return_value.text = fake_api_response 

        finalize_matches()

        # Debugging: Check if the mock was called
        mock_requests_get.assert_called()

        # Refresh all instances
        self.match_1.refresh_from_db()
        self.match_2.refresh_from_db()
        self.match_result_1.refresh_from_db()
        self.match_result_2.refresh_from_db()
        self.match_result_3.refresh_from_db()
        self.match_result_4.refresh_from_db()
        self.match_result_5.refresh_from_db()

        original_match_result = MatchResult.objects.filter(original_result=True)
        self.assertTrue(original_match_result.exists())
        self.assertEqual(self.match_1.match_state, Match.FINALIZED_MATCH)
        self.assertEqual(self.match_result_1.points, 3)
        self.assertEqual(self.match_result_2.points, 0)
        self.assertEqual(self.match_result_3.points, 1)
        self.assertEqual(self.match_result_4.points, 0)
        self.assertEqual(self.match_result_5.points, 0)
        self.assertEqual(self.match_result_1.is_exact, True)
        self.assertEqual(self.match_result_3.is_exact, False)
        self.assertEqual(self.match_result_4.is_exact, False)


class UpdateMatchesStartDate(TestCase):
    def setUp(self):
        self.tomorrow = now() + timedelta(days=1)
        self.in_12_hs = now() + timedelta(hours=12)
        self.two_hs_less = now() - timedelta(hours=2)
        self.league = LeagueFactory(slug='Update Matches')
        self.round = RoundFactory(league=self.league, start_date=self.tomorrow)
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.match_1 = MatchFactory(
            round=self.round, 
            team_1=self.team_1, 
            team_2=self.team_2, 
            start_date=None,
            match_state=Match.NOT_STARTED_MATCH
        )
        self.match_2 = MatchFactory(
            round=self.round, 
            team_1=self.team_3, 
            team_2=self.team_4,
            start_date=self.in_12_hs,
            match_state=Match.NOT_STARTED_MATCH
        )
        self.match_3 = MatchFactory(
            round=self.round,
            team_1=self.team_1,
            team_2=self.team_3,
            start_date=self.two_hs_less,
            match_state=Match.NOT_STARTED_MATCH
        )
        self.match_4 = MatchFactory(
            round=self.round,
            team_1=self.team_2,
            team_2=self.team_4,
            start_date=self.in_12_hs,
            match_state=Match.PENDING_MATCH
        )

    @patch('apps.match.tasks.requests.get')
    def test_update_matches_start_date(self, mock_requests_get):
        """
            Test that matches start dates and round start dates are updated successfully
        """
        new_start_date = now() + timedelta(hours=6)
        
        # Create a mock API response
        fake_api_response = f"""{{
            "response": [{{
                "fixture": {{"date": "{new_start_date}"}} 
            }}]
        }}"""

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get.return_value.text = fake_api_response
        mock_requests_get.return_value.text = fake_api_response 

        update_matches_start_date()

        # Debugging: Check if the mock was called
        mock_requests_get.assert_called()

        # Refresh all instances
        self.match_1.refresh_from_db()
        self.match_2.refresh_from_db()
        self.match_3.refresh_from_db()
        self.match_4.refresh_from_db()
        self.round.refresh_from_db()

        self.assertEqual(self.match_2.start_date, new_start_date)
        self.assertEqual(self.match_3.start_date, self.two_hs_less)
        self.assertEqual(self.round.start_date, self.two_hs_less)
        self.assertEqual(self.match_1.start_date, new_start_date)
        self.assertEqual(self.match_4.start_date, self.in_12_hs)


class CheckSuspendedMatchesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory(name='Suspended Matches Testing')
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.round = RoundFactory(league=self.league)
        self.match_1 = MatchFactory(
            team_1=self.team_1, 
            team_2=self.team_2, 
            match_state=Match.PENDING_MATCH,
            round=self.round,
            start_date=now()-timedelta(hours=5),
            api_match_id=1
        )
        self.match_2 = MatchFactory(
            team_1=self.team_3, 
            team_2=self.team_4, 
            match_state=Match.NOT_STARTED_MATCH,
            round=self.round,
            start_date=now()+timedelta(minutes=25),
            api_match_id=2
        )

    @patch('apps.match.tasks.requests.get')
    def test_sends_email_for_suspended_match(self, mock_requests_get):
        """
            Test that an email is sent when a match is suspended
        """
        # Create a mock API response
        fake_api_response = f"""{{
            "response": [{{
                "fixture": {{
                    "status": {{
                        "short": "SUSP"
                    }}
                }} 
            }}]
        }}"""

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get.return_value.text = fake_api_response
        mock_requests_get.return_value.text = fake_api_response 

        check_suspended_matches()

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(f'Match ID: {self.match_1.id}', email.body)
        self.assertIn('Reported Status: SUSP', email.body)


    @patch('apps.match.tasks.requests.get')
    def test_no_email_sent_for_non_suspended_match(self, mock_requests_get):
        """
            Test that no email is sent when a match is not suspended
        """
        # Create a mock API response
        fake_api_response = f"""{{
            "response": [{{
                "fixture": {{
                    "status": {{
                        "short": "FT"
                    }}
                }} 
            }}]
        }}"""

        # Configure the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.get.return_value.text = fake_api_response
        mock_requests_get.return_value.text = fake_api_response 

        check_suspended_matches()

        self.assertEqual(len(mail.outbox), 0)