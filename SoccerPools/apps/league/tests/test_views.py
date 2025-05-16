from rest_framework import status
from rest_framework.test import APITestCase
from apps.league.factories import LeagueFactory, RoundFactory
from apps.league.models import Round, League


class LeagueListTest(APITestCase):
    def setUp(self):
        self.league_1 = LeagueFactory(name='League Finalized', league_state=League.FINALIZED_LEAGUE)
        self.league_2 = LeagueFactory(name='League Americas', continent=League.AMERICAS)
        self.league_3 = LeagueFactory(name='League Tournaments', continent=League.TOURNAMENTS)
        self.league_4 = LeagueFactory(
            name='League Africa', 
            continent=League.AFRICA, 
            league_state=League.PENDING_LEAGUE
        )
        self.url = '/api/leagues/league/?continent='

    def test_league_list(self):
        """Test that all leagues except the finalized one are returned"""
        url = f'{self.url}6'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), League.objects.count()-1)
    
    def test_league_list_continent(self):
        """Test that leagues are filtered by continent"""
        url = f'{self.url}{str(League.AMERICAS)}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].get('id'), self.league_2.id)


class RoundListTest(APITestCase):
    def setUp(self):
        self.league = LeagueFactory(name='League Rounds Test')
        self.round_general = RoundFactory(league=self.league, number_round=0, is_general_round=True)
        self.round_1 = RoundFactory(league=self.league, number_round=1)
        self.round_4 = RoundFactory(league=self.league, number_round=4)
        self.round_2 = RoundFactory(league=self.league, number_round=2)
        self.round_3 = RoundFactory(league=self.league, number_round=3)
        self.round_5 = RoundFactory(league=self.league, number_round=5)

    def test_round_list(self):
        """Test that all rounds are returned in proper order"""
        url = f'/api/leagues/rounds/league/{self.league.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Round.objects.count()-1)
        for i, round in enumerate(response.data):
            if i != len(response.data)-1:
                self.assertTrue(round.get('number_round') < response.data[i+1].get('number_round'))

    def test_round_list_no_general_round(self):
        url = f'/api/leagues/rounds/league/{self.league.id}/?not_general_round=true'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Round.objects.count()-1)
        for i, round in enumerate(response.data):
            if i != len(response.data)-1:
                self.assertTrue(round.get('number_round') < response.data[i+1].get('number_round'))