from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apps.app_user.models import CoinGrant
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.match.models import MatchResult
from apps.bet.models import BetRound, BetLeague

User = get_user_model()

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
        response = self.client.post(add_coins_url, {'coins': CoinGrant.AD_REWARD_AMOUNT})
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.coins, 3010)

    def test_add_coins_no_coins(self):
        add_coins_url = f'{self.url}add_coins/'
        response = self.client.post(add_coins_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)

    def test_add_coins_invalid_reward_type(self):
        add_coins_url = f'{self.url}add_coins/'
        response = self.client.post(add_coins_url, {'coins': 10, 'reward_type': 10})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)

    def test_add_coins_invalid_coins(self):
        add_coins_url = f'{self.url}add_coins/'
        response = self.client.post(add_coins_url, {'coins': 5, 'reward_type': CoinGrant.AD_REWARD})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)

    def test_add_coins_existing_app_review_reward(self):
        add_coins_url = f'{self.url}add_coins/'
        CoinGrant.objects.create(
            user=self.user,
            reward_type=CoinGrant.APP_REVIEW,
            amount=CoinGrant.APP_REVIEW_AMOUNT
        )
        response = self.client.post(add_coins_url, {
            'coins': CoinGrant.APP_REVIEW_AMOUNT, 'reward_type': CoinGrant.APP_REVIEW
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)

    def test_add_coins_ad_reward_over_daily_cap(self):
        add_coins_url = f'{self.url}add_coins/'
        for _ in range(CoinGrant.AD_REWARD_DAILY_CAP):
            CoinGrant.objects.create(
                user=self.user, reward_type=CoinGrant.AD_REWARD, amount=CoinGrant.AD_REWARD_AMOUNT
            )
        response = self.client.post(add_coins_url, {
            'coins': CoinGrant.AD_REWARD_AMOUNT, 'reward_type': CoinGrant.AD_REWARD
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 3000)

    def test_members(self):
        member_url = f'{self.url}members/'
        user_1 = AppUserFactory()
        user_2 = AppUserFactory(username='user_2', referred_by=self.user)
        user_3 = AppUserFactory(username='user_3', referred_by=self.user)
        user_4 = AppUserFactory(referred_by=user_1)
        user_5 = AppUserFactory()

        response = self.client.get(member_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0].get('username'), user_2.username)
        self.assertEqual(response.data[1].get('username'), user_3.username)


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


class GoogleLoginViewTest(APITestCase):
    def setUp(self):
        self.url = '/api/user/google_oauth2/'
        self.legacy_url = '/api/user/android_google_oauth2/'

    def test_missing_access_token(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('apps.app_user.views.requests.get')
    def test_invalid_audience_rejected(self, mock_get):
        """Token with wrong audience should be rejected"""
        token_info_response = MagicMock()
        token_info_response.status_code = 200
        token_info_response.json.return_value = {'aud': 'some-other-app-client-id'}
        mock_get.return_value = token_info_response

        response = self.client.post(self.url, {'accessToken': 'fake-token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('access_token', response.data.get('errors', response.data))

    @patch('apps.app_user.views.requests.get')
    @patch('apps.app_user.views.add_google_picture_app_user')
    def test_valid_google_login_creates_user(self, mock_picture, mock_get):
        """Valid Google token should create user and return JWT tokens"""
        token_info_response = MagicMock()
        token_info_response.status_code = 200
        token_info_response.json.return_value = {
            'aud': '758848666906-of896o3nh91kutmk5dinhja0tsjftscs.apps.googleusercontent.com'
        }

        user_info_response = MagicMock()
        user_info_response.status_code = 200
        user_info_response.json.return_value = {
            'email': 'newuser@gmail.com',
            'given_name': 'Test',
            'family_name': 'User',
            'name': 'Test User',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg',
        }

        mock_get.side_effect = [token_info_response, user_info_response]

        response = self.client.post(self.url, {'accessToken': 'valid-google-token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(User.objects.filter(email='newuser@gmail.com').exists())

    @patch('apps.app_user.views.requests.get')
    @patch('apps.app_user.views.add_google_picture_app_user')
    def test_existing_user_login(self, mock_picture, mock_get):
        """Existing user should get tokens without creating a duplicate"""
        User.objects.create_user(
            username='existinguser', email='existing@gmail.com',
            name='Existing', last_name='User', password='testpass123'
        )

        token_info_response = MagicMock()
        token_info_response.status_code = 200
        token_info_response.json.return_value = {
            'aud': '758848666906-of896o3nh91kutmk5dinhja0tsjftscs.apps.googleusercontent.com'
        }

        user_info_response = MagicMock()
        user_info_response.status_code = 200
        user_info_response.json.return_value = {
            'email': 'existing@gmail.com',
            'given_name': 'Existing',
            'family_name': 'User',
            'name': 'Existing User',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg',
        }

        mock_get.side_effect = [token_info_response, user_info_response]

        response = self.client.post(self.url, {'accessToken': 'valid-google-token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(email='existing@gmail.com').count(), 1)

    @patch('apps.app_user.views.requests.get')
    @patch('apps.app_user.views.add_google_picture_app_user')
    def test_legacy_endpoint_still_works(self, mock_picture, mock_get):
        """The old android_google_oauth2 endpoint should still work"""
        token_info_response = MagicMock()
        token_info_response.status_code = 200
        token_info_response.json.return_value = {
            'aud': '758848666906-of896o3nh91kutmk5dinhja0tsjftscs.apps.googleusercontent.com'
        }

        user_info_response = MagicMock()
        user_info_response.status_code = 200
        user_info_response.json.return_value = {
            'email': 'legacy@gmail.com',
            'given_name': 'Legacy',
            'family_name': 'User',
            'name': 'Legacy User',
            'picture': 'https://lh3.googleusercontent.com/photo.jpg',
        }

        mock_get.side_effect = [token_info_response, user_info_response]

        response = self.client.post(self.legacy_url, {'accessToken': 'valid-google-token'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
