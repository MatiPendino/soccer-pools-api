from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from django.utils.timezone import now, timedelta
from apps.league.factories import LeagueFactory, RoundFactory
from apps.league.models import Round
from apps.league.tasks import check_upcoming_rounds

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