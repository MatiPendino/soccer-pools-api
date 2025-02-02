from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.db.models import Sum
from apps.app_user.factories import AppUserFactory
from apps.match.factories import MatchFactory, MatchResultFactory
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.tournament.factories import TournamentFactory, TournamentUserFactory
from apps.bet.factories import BetFactory
from apps.bet.models import Bet
from apps.match.models import MatchResult
from apps.tournament.models import TournamentUser

class BetResultsTest(APITestCase):
    def setUp(self):
        self.user_1 = AppUserFactory(email='user1@gmail.com', username='user1')
        self.user_2 = AppUserFactory(email='user2@gmail.com', username='user2')
        self.league = LeagueFactory()
        self.round_general = RoundFactory(league=self.league, is_general_round=True)
        self.round_1 = RoundFactory(league=self.league)
        self.round_2 = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league)
        self.team_2 = TeamFactory(league=self.league)
        self.team_3 = TeamFactory(league=self.league)
        self.team_4 = TeamFactory(league=self.league)
        self.team_5 = TeamFactory(league=self.league)
        self.team_6 = TeamFactory(league=self.league)
        self.match_1 = MatchFactory(round=self.round_1, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round_1, team_1=self.team_3, team_2=self.team_4)
        self.match_3 = MatchFactory(round=self.round_1, team_1=self.team_5, team_2=self.team_6)
        self.match_4 = MatchFactory(round=self.round_2, team_1=self.team_1, team_2=self.team_3)
        self.match_5 = MatchFactory(round=self.round_2, team_1=self.team_2, team_2=self.team_4)
        self.match_6 = MatchFactory(round=self.round_2, team_1=self.team_3, team_2=self.team_6)
        self.bet_general_user_1 = BetFactory(user=self.user_1, round=self.round_general)
        self.bet_general_user_2 = BetFactory(user=self.user_2, round=self.round_general)
        self.bet_1 = BetFactory(user=self.user_1, round=self.round_1)
        self.bet_2 = BetFactory(user=self.user_2, round=self.round_1)
        self.bet_3 = BetFactory(user=self.user_2, round=self.round_2)
        self.bet_4 = BetFactory(user=self.user_2, round=self.round_2)
        self.match_result_1 = MatchResultFactory(bet=self.bet_1, match=self.match_1, points=1)
        self.match_result_2 = MatchResultFactory(bet=self.bet_1, match=self.match_2, points=0)
        self.match_result_3 = MatchResultFactory(bet=self.bet_1, match=self.match_3, points=0)
        self.match_result_4 = MatchResultFactory(bet=self.bet_2, match=self.match_1, points=0)
        self.match_result_5 = MatchResultFactory(bet=self.bet_2, match=self.match_2, points=3)
        self.match_result_6 = MatchResultFactory(bet=self.bet_2, match=self.match_3, points=1)
        self.match_result_7 = MatchResultFactory(bet=self.bet_3, match=self.match_4, points=1)
        self.match_result_8 = MatchResultFactory(bet=self.bet_3, match=self.match_5, points=0)
        self.match_result_9 = MatchResultFactory(bet=self.bet_3, match=self.match_6, points=0)
        self.match_result_10 = MatchResultFactory(bet=self.bet_4, match=self.match_4, points=0)
        self.match_result_11 = MatchResultFactory(bet=self.bet_4, match=self.match_5, points=3)
        self.match_result_12 = MatchResultFactory(bet=self.bet_4, match=self.match_6, points=1)
        self.client.force_authenticate(user=self.user_1)

    def test_bet_results_no_tournament(self):
        """Test that we receive the proper bets ordered by points"""
        round_slug = self.round_1.slug
        url = f'/api/bets/bet_results/{round_slug}/0/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data[0].get('points') >= response.data[1].get('points'))
        self.assertEqual(len(response.data), Bet.objects.filter(round__slug=round_slug).count())

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
            Bet.objects.filter(round__is_general_round=True).count()
        )

        # Calculate the total points of each bet in memory and test that matches the points
        # retrived from the response
        for i, bet in enumerate(response.data):
            total_points = Bet.objects.filter(
                state=True, 
                round__is_general_round=False,
                user__username=bet.get('username')
            ).aggregate(
                points=Sum('match_result__points')
            )['points'] or 0

            self.assertEqual(response.data[i].get('points'), total_points)


        
class LeagueBetsMatchResultsCreateTest(APITestCase):
    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory(name='My League')
        self.round_1 = RoundFactory(league=self.league)
        self.round_2 = RoundFactory(league=self.league)
        self.team_1 = TeamFactory(league=self.league)
        self.team_2 = TeamFactory(league=self.league)
        self.team_3 = TeamFactory(league=self.league)
        self.team_4 = TeamFactory(league=self.league)
        self.team_5 = TeamFactory(league=self.league)
        self.team_6 = TeamFactory(league=self.league)
        self.match_1 = MatchFactory(round=self.round_1, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round_1, team_1=self.team_3, team_2=self.team_4)
        self.match_3 = MatchFactory(round=self.round_1, team_1=self.team_5, team_2=self.team_6)
        self.match_4 = MatchFactory(round=self.round_2, team_1=self.team_1, team_2=self.team_3)
        self.match_5 = MatchFactory(round=self.round_2, team_1=self.team_2, team_2=self.team_4)
        self.match_6 = MatchFactory(round=self.round_2, team_1=self.team_3, team_2=self.team_6)
        self.url = '/api/bets/league_bets_create/'

    def test_league_bets_creation(self):
        """
            Test that all the Bets and MatchResults are created for the user based on the league
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'league_slug': self.league.slug,
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Bet.objects.count(), 2)
        self.assertEqual(MatchResult.objects.count(), 6)