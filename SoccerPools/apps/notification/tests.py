from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.bet.factories import BetLeagueFactory
from apps.league.factories import LeagueFactory
from apps.notification.models import FCMToken
from apps.notification.serializers import FCMTokenSerializer

User = get_user_model()
class FCMTokenAPIViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='matiem',
            email='matiemail@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )
        self.client.force_authenticate(user=self.user)
        self.league_one = LeagueFactory()
        self.league_two = LeagueFactory()
        self.bet_league_one = BetLeagueFactory(user=self.user, league=self.league_one)
        self.bet_league_two = BetLeagueFactory(user=self.user, league=self.league_two)
        self.token_id = 'exampletoken'
        self.url = reverse('fcm_device')

    def test_created_fcm_token(self):
        data = {
            'fcm_token': self.token_id
        }
        response = self.client.post(self.url, data=data, format='json')
        fcm_token = FCMToken.objects.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, FCMTokenSerializer(fcm_token).data)

    def test_retrieved_fcm_token(self):
        fcm_token = FCMToken.objects.create(
            token_id=self.token_id,
            user=self.user
        )
        fcm_token.leagues.add(self.league_one, self.league_two)
        data = {
            'fcm_token': self.token_id
        }
        response = self.client.post(self.url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, FCMTokenSerializer(fcm_token).data)
