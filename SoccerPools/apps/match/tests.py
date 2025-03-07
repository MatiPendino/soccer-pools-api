from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.match.models import MatchResult, Match
from apps.match.serializers import MatchResultSerializer
from .factories import MatchResultFactory, MatchFactory
from .tasks import check_upcoming_matches, finalize_matches

User = get_user_model()
class MatchResultsListCreateTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@gmail.com',
            name='TestName',
            last_name='TestSurname'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league, name='Rosario Central')
        self.team_2 = TeamFactory(league=self.league, name='NOB')
        self.team_3 = TeamFactory(league=self.league, name='River Plate')
        self.bet_league = BetLeagueFactory(league=self.league, user=self.user)
        self.bet_round = BetRoundFactory(round=self.round, bet_league=self.bet_league)
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_3)
        self.match_result_1 = MatchResultFactory(bet_round=self.bet_round, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet_round=self.bet_round, match=self.match_2)
        self.url = '/api/matches/match_results/'

    def test_get_match_results(self):
        """Test that the GET request retrieves match results filtered by round_id"""
        response = self.client.get(self.url, {'round_id': self.bet_round.round.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], self.match_result_1.id)


class MatchResultsUpdateTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@gmail.com',
            name='TestName',
            last_name='TestSurname'
        )
        self.client.login(username='testuser', password='testpassword')

        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league, name='Rosario Central')
        self.team_2 = TeamFactory(league=self.league, name='NOB')
        self.team_3 = TeamFactory(league=self.league, name='River Plate')
        self.bet_league = BetLeagueFactory(league=self.league, user=self.user)
        self.bet_round = BetRoundFactory(round=self.round, bet_league=self.bet_league)
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_3)
        self.match_result_1 = MatchResultFactory(bet_round=self.bet_round, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet_round=self.bet_round, match=self.match_2)
        self.url = '/api/matches/match_results_update/'

    def test_updated_results(self):
        """Test that a POST request updates the current match results"""
        matchResults = [
            {
                'badge_team_1': '', 'badge_team_2': '', 'goals_team_1': 1, 'team_2': self.team_2.name,
                'goals_team_2': 2, 'id': self.match_result_1.id, 'team_1': self.team_1.name,
            },
            {
                'badge_team_1': '', 'badge_team_2': '', 'goals_team_1': 5, 'team_2': self.team_3.name,
                'goals_team_2': 5, 'id': self.match_result_2.id, 'team_1': self.team_1.name,
            }
        ]

        data = {
            'matchResults': matchResults
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.match_result_1.refresh_from_db()
        self.match_result_2.refresh_from_db()
        self.assertEqual(
            self.match_result_1.goals_team_1, 
            matchResults[0].get('goals_team_1')
        )
        self.assertEqual(
            self.match_result_2.goals_team_2, 
            matchResults[1].get('goals_team_2')
        )


class MatchResultOriginalTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@gmail.com',
            name='TestName',
            last_name='TestSurname'
        )
        self.client.login(username='testuser', password='testpassword')

        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league, name='Rosario Central')
        self.team_2 = TeamFactory(league=self.league, name='NOB')
        self.bet_league = BetLeagueFactory(league=self.league, user=self.user)
        self.bet_round = BetRoundFactory(bet_league=self.bet_league, round=self.round)
        self.match = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_result_user = MatchResultFactory(bet_round=self.bet_round, match=self.match)
        self.match_result_original = MatchResult.objects.create(
            original_result=True,
            match=self.match
        )
        self.url = f'/api/matches/original_match_result/{self.match.id}/'

    def test_get_original_match_result(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, MatchResultSerializer(self.match_result_original).data)

    def test_get_no_existing_original_match_result(self):
        self.match_result_original.original_result = False
        self.match_result_original.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, None)

    def test_get_no_existing_match_id(self):
        response = self.client.get('/api/matches/original_match_result/54454/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UpcomingMatchesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory()
        self.team_1 = TeamFactory(league=self.league)
        self.team_2 = TeamFactory(league=self.league)
        self.team_3 = TeamFactory(league=self.league)
        self.team_4 = TeamFactory(league=self.league)
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
        upcoming_matches = check_upcoming_matches()
        self.match_1.refresh_from_db()
        self.match_2.refresh_from_db()
        self.match_3.refresh_from_db()
        self.match_4.refresh_from_db()
        self.assertEqual(upcoming_matches.count(), 2)
        self.assertEqual(self.match_1.match_state, Match.PENDING_MATCH)
        self.assertEqual(self.match_4.match_state, Match.PENDING_MATCH)


class FinalizeMatchesTest(TestCase):
    def setUp(self):
        self.league = LeagueFactory(name='Finalize Testing')
        self.team_1 = TeamFactory(league=self.league)
        self.team_2 = TeamFactory(league=self.league)
        self.team_3 = TeamFactory(league=self.league)
        self.team_4 = TeamFactory(league=self.league)
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

        original_match_result = MatchResult.objects.filter(original_result=True)
        self.assertTrue(original_match_result.exists())
        self.assertEqual(self.match_1.match_state, Match.FINALIZED_MATCH)
        self.assertEqual(self.match_result_1.points, 3)
        self.assertEqual(self.match_result_2.points, 0)
        self.assertEqual(self.match_result_3.points, 1)
        self.assertEqual(self.match_result_4.points, 0)