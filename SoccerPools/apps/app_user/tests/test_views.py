from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.match.models import MatchResult
from apps.bet.models import BetRound, BetLeague

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
        with self.assertRaises(ValidationError):
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = AppUserFactory(
            username='testuser',
            coins=3000
        )
        self.client.force_authenticate(user=self.user)
        self.url = '/api/user/user/'

    def test_add_coins(self):
        add_coins_url = f'{self.url}add_coins/'
        response = self.client.post(add_coins_url, {'coins': 1000})
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.coins, 4000)

    def test_add_coins_invalid(self):
        add_coins_url = f'{self.url}add_coins/'
        with self.assertRaises(ValidationError):
            response = self.client.post(add_coins_url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)


class UserInLeagueTest(APITestCase):
    def setUp(self):
        self.user = AppUserFactory(email='user@gmail.com')
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(leagues=[self.league], name='Rosario Central')
        self.team_2 = TeamFactory(leagues=[self.league], name='NOB')
        self.url = f'/api/user/user_in_league/'

    def test_user_in_league(self):
        self.bet_league = BetLeagueFactory(league=self.league, user=self.user)
        self.bet_round = BetRoundFactory(round=self.round)
        self.match = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('in_league'))

    def test_user_not_in_league(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('in_league'))


class LeagueUserTest(APITestCase):
    def setUp(self):
        self.user = AppUserFactory(email='leagueuser@gmail.com')
        self.league = LeagueFactory(name='Liga Argentina')
        self.league_2 = LeagueFactory(name='Liga Chilena')
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(leagues=[self.league], name='Rosario Central')
        self.team_2 = TeamFactory(leagues=[self.league], name='NOB')
        self.url = f'/api/user/user_league/'

    def test_user_league_last_visited(self):
        self.bet_league = BetLeagueFactory(
            user=self.user, league=self.league, is_last_visited_league=True
        )
        self.bet_league_2 = BetLeagueFactory(
            user=self.user, league=self.league_2, is_last_visited_league=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data.get('name'), self.league_2.name)
        self.assertEqual(response.data.get('name'), self.league.name)

    def test_user_league_not_last_visited(self):
        self.bet_league = BetLeagueFactory(
            user=self.user, league=self.league, is_last_visited_league=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.bet_league.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.league.name)
        self.assertTrue(self.bet_league.is_last_visited_league)


class RemoveUserSetUp(APITestCase):
    def setUp(self):
        self.username = 'mati'
        self.password = '123456798'
        self.user = User.objects.create_user(
            username=self.username,
            email='email@gmail.com',
            name='Mati',
            last_name='Pendino',
            password=self.password
        )
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(name='Team 1', leagues=[self.league])
        self.team_2 = TeamFactory(name='Team 2', leagues=[self.league])
        self.team_3 = TeamFactory(name='Team 3', leagues=[self.league])
        self.team_4 = TeamFactory(name='Team 4', leagues=[self.league])
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_3, team_2=self.team_4)
        self.bet_league = BetLeagueFactory(user=self.user, league=self.league)
        self.bet_round = BetRoundFactory(round=self.round, bet_league=self.bet_league)
        self.match_result_1 = MatchResultFactory(bet_round=self.bet_round, match=self.match_1)
        self.match_result_2 = MatchResultFactory(bet_round=self.bet_round, match=self.match_2)

class UserDestroyTest(RemoveUserSetUp):
    def test_destroy_user(self):
        """
            Test that the user and its corresponding MatchResults and Bets are removed successfully
        """
        self.url = '/api/user/user_destroy/'
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(MatchResult.objects.filter(state=True).count(), 0)
        self.assertEqual(BetLeague.objects.filter(state=True).count(), 0)
        self.assertEqual(BetRound.objects.filter(state=True).count(), 0)


class RemoveUserTest(RemoveUserSetUp):
    def test_remove_user(self):
        """
            Test that the user and its corresponding MatchResults and Bets are removed successfully
        """
        self.url = '/api/user/remove_user/'
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.url, data)
        self.assertEqual(MatchResult.objects.filter(state=True).count(), 0)
        self.assertEqual(BetLeague.objects.filter(state=True).count(), 0)
        self.assertEqual(BetRound.objects.filter(state=True).count(), 0)
