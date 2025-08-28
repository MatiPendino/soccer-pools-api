from rest_framework.test import APIClient, APITestCase
from rest_framework import status
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
