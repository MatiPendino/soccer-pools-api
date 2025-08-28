from rest_framework.test import APITestCase
from rest_framework import status
from django.db.models import Sum
from django.core.exceptions import ValidationError
from apps.app_user.factories import AppUserFactory
from apps.app_user.models import AppUser
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.tournament.factories import TournamentFactory, TournamentUserFactory
from apps.bet.factories import BetRoundFactory, BetLeagueFactory
from apps.league.models import League, Round
from apps.bet.models import BetLeague, BetRound
from apps.match.models import MatchResult
from apps.tournament.models import TournamentUser

class BetRoundResultsTest(APITestCase):
    def setUp(self):
        self.user_1 = AppUser.objects.create_user(
            username='matias',
            email='matias@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456789'
        )
        self.user_2 = AppUser.objects.create_user(
            username='mati',
            email='mati@gmail.com',
            name='Matias',
            last_name='Pendino',
            password='123456789'
        )
        self.league = LeagueFactory()
        self.round_general = RoundFactory(league=self.league, is_general_round=True)
        self.round_1 = RoundFactory(league=self.league)
        self.round_2 = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.team_5 = TeamFactory(leagues=[self.league])
        self.team_6 = TeamFactory(leagues=[self.league])
        self.match_1 = MatchFactory(round=self.round_1, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round_1, team_1=self.team_3, team_2=self.team_4)
        self.match_3 = MatchFactory(round=self.round_1, team_1=self.team_5, team_2=self.team_6)
        self.match_4 = MatchFactory(round=self.round_2, team_1=self.team_1, team_2=self.team_3)
        self.match_5 = MatchFactory(round=self.round_2, team_1=self.team_2, team_2=self.team_4)
        self.match_6 = MatchFactory(round=self.round_2, team_1=self.team_3, team_2=self.team_6)
        self.bet_league_1 = BetLeagueFactory(user=self.user_1, league=self.league)
        self.bet_league_2 = BetLeagueFactory(user=self.user_2, league=self.league)
        self.bet_round_general_user_1 = BetRoundFactory(bet_league=self.bet_league_1, round=self.round_general)
        self.bet_round_general_user_2 = BetRoundFactory(bet_league=self.bet_league_2, round=self.round_general)
        self.bet_round_1 = BetRoundFactory(bet_league=self.bet_league_1, round=self.round_1)
        self.bet_round_2 = BetRoundFactory(bet_league=self.bet_league_2, round=self.round_1)
        self.bet_round_3 = BetRoundFactory(bet_league=self.bet_league_2, round=self.round_2)
        self.bet_round_4 = BetRoundFactory(bet_league=self.bet_league_2, round=self.round_2)
        self.match_result_1 = MatchResultFactory(bet_round=self.bet_round_1, match=self.match_1, points=1)
        self.match_result_2 = MatchResultFactory(bet_round=self.bet_round_1, match=self.match_2, points=0)
        self.match_result_3 = MatchResultFactory(bet_round=self.bet_round_1, match=self.match_3, points=0)
        self.match_result_4 = MatchResultFactory(bet_round=self.bet_round_2, match=self.match_1, points=0)
        self.match_result_5 = MatchResultFactory(bet_round=self.bet_round_2, match=self.match_2, points=3)
        self.match_result_6 = MatchResultFactory(bet_round=self.bet_round_2, match=self.match_3, points=1)
        self.match_result_7 = MatchResultFactory(bet_round=self.bet_round_3, match=self.match_4, points=1)
        self.match_result_8 = MatchResultFactory(bet_round=self.bet_round_3, match=self.match_5, points=0)
        self.match_result_9 = MatchResultFactory(bet_round=self.bet_round_3, match=self.match_6, points=0)
        self.match_result_10 = MatchResultFactory(bet_round=self.bet_round_4, match=self.match_4, points=0)
        self.match_result_11 = MatchResultFactory(bet_round=self.bet_round_4, match=self.match_5, points=3)
        self.match_result_12 = MatchResultFactory(bet_round=self.bet_round_4, match=self.match_6, points=1)
        self.client.force_authenticate(user=self.user_1)

    def test_bet_results_no_tournament(self):
        """Test that we receive the proper bets ordered by points"""
        round_slug = self.round_1.slug
        url = f'/api/bets/bet_results/{round_slug}/0/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data[0].get('points') >= response.data[1].get('points'))
        self.assertEqual(len(response.data), BetRound.objects.filter(round__slug=round_slug).count())

    def test_bet_results_tournament(self):
        """
            Test that all the ACCEPTED bets for the tournament users are returned
        """
        tournament = TournamentFactory(league=self.league, admin_tournament=self.user_1)
        tournament_user_accepted = TournamentUserFactory(
            tournament=tournament, 
            user=self.user_1,
            tournament_user_state=TournamentUser.ACCEPTED,    
        )
        # TournamentUser not accepted, should not be returned
        tournament_user_not_accepted = TournamentUserFactory(
            tournament=tournament, 
            user=self.user_2,
        )
        url = f'/api/bets/bet_results/{self.round_1.slug}/{tournament.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(len(response.data) == TournamentUser.objects.count())
        self.assertTrue(
            len(response.data) == 
            TournamentUser.objects.filter(tournament_user_state=TournamentUser.ACCEPTED).count()
        )

    def test_bet_general_round(self):
        """
            Test that the endpoint returns the general bets ordered by their accumulated total points
        """
        url = f'/api/bets/bet_results/{self.round_general.slug}/0/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data[0].get('points') >= response.data[1].get('points'))
        self.assertEqual(
            len(response.data), 
            BetRound.objects.filter(round__is_general_round=True).count()
        )

        # Calculate the total points of each bet in memory and test that matches the points
        # retrived from the response
        for i, bet in enumerate(response.data):
            total_points = BetRound.objects.filter(
                state=True, 
                round__is_general_round=False,
                bet_league__user__username=bet.get('username')
            ).aggregate(
                points=Sum('match_results__points')
            )['points'] or 0

            self.assertEqual(response.data[i].get('points'), total_points)


        
class LeagueBetsMatchResultsCreateTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        LeagueFactory(name='My League', slug='babosa', coins_cost=1000)

    def setUp(self):
        self.user = AppUserFactory(email='leaguebets@gmail.com', coins=1500)
        self.league = League.objects.first()
        self.round_1 = RoundFactory(league=self.league)
        self.round_2 = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(leagues=[self.league])
        self.team_2 = TeamFactory(leagues=[self.league])
        self.team_3 = TeamFactory(leagues=[self.league])
        self.team_4 = TeamFactory(leagues=[self.league])
        self.team_5 = TeamFactory(leagues=[self.league])
        self.team_6 = TeamFactory(leagues=[self.league])
        self.match_1 = MatchFactory(round=self.round_1, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round_1, team_1=self.team_3, team_2=self.team_4)
        self.match_3 = MatchFactory(round=self.round_1, team_1=self.team_5, team_2=self.team_6)
        self.match_4 = MatchFactory(round=self.round_2, team_1=self.team_1, team_2=self.team_3)
        self.match_5 = MatchFactory(round=self.round_2, team_1=self.team_2, team_2=self.team_4)
        self.match_6 = MatchFactory(round=self.round_2, team_1=self.team_3, team_2=self.team_6)
        self.url = '/api/bets/league_bets_create/'

    def test_league_bets_creation(self):
        """
            Test that all the BetLeague, BetRound and MatchResult instances are created 
            for the user based on the league, and coins are substracted from the user
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'league_slug': self.league.slug,
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BetLeague.objects.count(), 1)
        self.assertEqual(BetRound.objects.count(), 2)
        self.assertEqual(BetRound.objects.first().bet_league, BetLeague.objects.first())
        self.assertEqual(MatchResult.objects.count(), 6)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 500)

    def test_already_created_bet_league(self):
        """
            Test that when there is an existing bet_league for the user and league we send,
            NO NEW BetLeague, BetRound or MatchResult instances are created
        """
        self.team_7 = TeamFactory(leagues=[self.league])
        self.team_8 = TeamFactory(leagues=[self.league])
        self.team_9 = TeamFactory(leagues=[self.league])
        self.team_10 = TeamFactory(leagues=[self.league])
        self.match_1 = MatchFactory(round=self.round_1, team_1=self.team_7, team_2=self.team_8)
        self.match_7 = MatchFactory(round=self.round_1, team_1=self.team_9, team_2=self.team_10)
        self.match_8 = MatchFactory(round=self.round_2, team_1=self.team_7, team_2=self.team_9)
        self.match_9 = MatchFactory(round=self.round_2, team_1=self.team_8, team_2=self.team_10)
        self.bet_league = BetLeagueFactory(user=self.user, league=self.league)
        self.bet_round_1 = BetRound.objects.create(round=self.round_1, bet_league=self.bet_league)
        self.bet_round_2 = BetRound.objects.create(round=self.round_2, bet_league=self.bet_league)
        self.match_result_1 = MatchResultFactory(bet_round=self.bet_round_1, match=self.match_8)
        self.match_result_2 = MatchResultFactory(bet_round=self.bet_round_2, match=self.match_9)

        self.client.force_authenticate(user=self.user)
        data = {
            'league_slug': self.league.slug,
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BetLeague.objects.count(), 1)
        self.assertEqual(BetRound.objects.count(), 2)
        self.assertEqual(BetRound.objects.first().bet_league, BetLeague.objects.first())
        self.assertEqual(MatchResult.objects.count(), 2)

    def test_finalized_round(self):
        """
            Test that NO BetRound or MatchResult instances are created for a Round that
            is on finalized round_state
        """
        self.round_3 = RoundFactory(league=self.league, round_state=Round.FINALIZED_ROUND)
        self.match_1 = MatchFactory(round=self.round_3, team_1=self.team_1, team_2=self.team_4)
        self.match_2 = MatchFactory(round=self.round_3, team_1=self.team_3, team_2=self.team_2)

        self.client.force_authenticate(user=self.user)
        data = {
            'league_slug': self.league.slug,
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BetLeague.objects.count(), 1)
        self.assertEqual(BetRound.objects.count(), 2)
        self.assertEqual(BetRound.objects.first().bet_league, BetLeague.objects.first())
        self.assertEqual(MatchResult.objects.count(), 6)

    def test_no_enough_coins(self):
        """
            Test that when the user does not have enough coins, a ValidationError is raised
        """
        self.user.coins = 0
        self.user.save()
        self.client.force_authenticate(user=self.user)
        data = {
            'league_slug': self.league.slug,
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.user.coins, 0)
        self.assertEqual(BetLeague.objects.count(), 0)

    def test_no_enough_coins_existing_bet_league(self):
        """
            Test that when the user does not have enough coins but is 
            already in that league, NO ValidationError is raised
        """
        self.user.coins = 0
        self.user.save()
        self.client.force_authenticate(user=self.user)
        bet_league = BetLeagueFactory(user=self.user, league=self.league)
        bet_round_1 = BetRound.objects.create(round=self.round_1, bet_league=bet_league)
        bet_round_2 = BetRound.objects.create(round=self.round_2, bet_league=bet_league)
        data = {
            'league_slug': self.league.slug,
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BetLeague.objects.count(), 1)
        self.assertEqual(BetRound.objects.count(), 2)
