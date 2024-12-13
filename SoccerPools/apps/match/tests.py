from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetFactory
from apps.match.models import MatchResult
from .factories import MatchResultFactory, MatchFactory

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
        self.client.login(username='testuser', password='testpassword')

        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league, name='Rosario Central')
        self.team_2 = TeamFactory(league=self.league, name='NOB')
        self.team_3 = TeamFactory(league=self.league, name='River Plate')
        self.bet = BetFactory(round=self.round, user=self.user)
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_3)
        self.match_result_1 = MatchResultFactory(bet=self.bet, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet=self.bet, match=self.match_2)
        self.url = '/api/matches/match_results/'

    def test_get_match_results(self):
        """Test that the GET request retrieves match results filtered by round_id"""
        response = self.client.get(self.url, {'round_id': self.bet.round.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], self.match_result_1.id)

    def test_create_match_results(self):
        """Test that a POST request creates new match results"""
        data = [
            {'goals_team_1': 3, 'goals_team_2': 2, 'match': self.match_1.id},
            {'goals_team_1': 0, 'goals_team_2': 1, 'match': self.match_2.id}
        ]

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(len(response.data), len(data))
        self.assertEqual(MatchResult.objects.count(), 4) # Two created in setUp, two new


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
        self.bet = BetFactory(round=self.round, user=self.user)
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_3)
        self.match_result_1 = MatchResultFactory(bet=self.bet, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet=self.bet, match=self.match_2)
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