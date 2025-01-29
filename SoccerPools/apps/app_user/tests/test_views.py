from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetFactory
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.match.models import MatchResult
from apps.bet.models import Bet

User = get_user_model()
class UserRegisterViewTest(TestCase):
    def setUp(self):
        self.register_url = reverse('user_register')
        self.client = APIClient()

    def test_user_registration_success(self):
        data = {
            'username': 'mati',
            'email': 'mati@gmail.com',
            'name': 'Matias',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_failure(self):
        data = {'username': 'fail'}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(
            username='mati',
            email='mati@gmail.com',
            name='Matias',
            last_name='Pendino',
            password='123456789'
        )

    def setUp(self):
        self.login_url = reverse('user_login')
        self.client = APIClient()

    def test_user_login_success(self):
        data = {
            'username': 'mati',
            'password': '123456789'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_login_failure(self):
        data = {
            'username': 'mati',
            'password': '12345678'
        }
        with self.assertRaises(ValueError):
            self.client.post(self.login_url, data, format='json')

    def test_missing_login_data(self):
        data_no_password = {'username': 'mati'}
        response = self.client.post(self.login_url, data_no_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data_no_username = {'password': '123456789'}
        response = self.client.post(self.login_url, data_no_username, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLogoutViewTest(TestCase):
    def setUp(self):
        self.logout_url = reverse('user_logout')
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='mati',
            email='email@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )

    def test_logout_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserViewTest(TestCase):
    def setUp(self):
        self.view_url = reverse('user_view')
        self.client = APIClient()

    def test_view_user_logged(self):
        user = User.objects.create_user(
            username='mati',
            email='email@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_user_not_logged(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserDestroyTest(APITestCase):
    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(name='Team 1', league=self.league)
        self.team_2 = TeamFactory(name='Team 2', league=self.league)
        self.team_3 = TeamFactory(name='Team 3', league=self.league)
        self.team_4 = TeamFactory(name='Team 4', league=self.league)
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_3, team_2=self.team_4)
        self.bet = BetFactory(user=self.user, round=self.round)
        self.match_result_1 = MatchResultFactory(bet=self.bet, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet=self.bet, match=self.match_2)
        self.url = '/api/user/user_destroy/'

    def test_destroy_user(self):
        """
            Test that the user and its corresponding MatchResults and Bets are removed successfully
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MatchResult.objects.filter(state=True).count(), 0)
        self.assertEqual(Bet.objects.filter(state=True).count(), 0)
        self.assertEqual(Bet.objects.filter(state=True).count(), 0)


