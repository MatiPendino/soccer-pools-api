from rest_framework import status
from rest_framework.test import APITestCase
from apps.league.factories import LeagueFactory, RoundFactory
from apps.league.models import Round

class RoundListTest(APITestCase):
    def setUp(self):
        self.league = LeagueFactory(name='League Rounds Test')
        self.round_1 = RoundFactory(league=self.league, number_round=1)
        self.round_4 = RoundFactory(league=self.league, number_round=4)
        self.round_2 = RoundFactory(league=self.league, number_round=2)
        self.round_3 = RoundFactory(league=self.league, number_round=3)
        self.round_5 = RoundFactory(league=self.league, number_round=5)
        self.url = f'/api/leagues/rounds/league/{self.league.id}/'

    def test_round_list(self):
        """Test that all rounds are returned in proper order"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Round.objects.count())
        for i, round in enumerate(response.data):
            if i != len(response.data)-1:
                self.assertTrue(round.get('number_round') < response.data[i+1].get('number_round'))
