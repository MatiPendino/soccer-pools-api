from rest_framework import status
from rest_framework.test import APITestCase
from apps.app_user.factories import AppUserFactory
from apps.prize.factories import PrizeFactory
from apps.prize.models import Prize, PrizeUser

class PrizeViewSetTest(APITestCase):
    def setUp(self):
        self.initial_coins = 50000
        self.prize_1 = PrizeFactory(coins_cost=10000)
        self.prize_2 = PrizeFactory(coins_cost=100000)
        self.user = AppUserFactory(coins=self.initial_coins)

    def test_prizes_list(self):
        """Test that are prizes are listed successfully"""
        url = '/api/prizes/prize/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), Prize.objects.count())

    def test_prize_user_valid(self):
        """Test that if user has enough coins, PrizeUser is created and coins are substracted"""
        url = f'/api/prizes/prize/{self.prize_1.id}/claim/'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PrizeUser.objects.count(), 1)
        self.assertEqual(self.user.coins, self.initial_coins - self.prize_1.coins_cost)

    def test_prize_user_not_enough_coins(self):
        """Test that if user does not have enough coins, PrizeUser is not created and coins are the same"""
        url = f'/api/prizes/prize/{self.prize_2.id}/claim/'
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(PrizeUser.objects.count(), 0)
        self.assertEqual(self.user.coins, self.initial_coins)