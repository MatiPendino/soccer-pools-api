from decimal import Decimal
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import TestCase
from apps.app_user.models import AppUser
from apps.app_user.factories import AppUserFactory
from apps.bet.models import BetLeague, BetRound
from apps.league.factories import LeagueFactory, RoundFactory, TeamFactory
from apps.league.models import Round
from apps.match.factories import MatchFactory
from apps.match.models import Match, MatchResult
from .models import Payment, PaidBetRound, PaidPrizePool, PaidWinner
from .factories import ( 
    PaidLeagueConfigFactory, PaymentFactory, PaidBetRoundFactory, PaidPrizePoolFactory,
)
from .services import (
    calculate_payment_amounts, create_round_payment, create_league_payment,
    process_approved_payment, distribute_round_prizes, update_payment_from_webhook,
)
from .tasks import update_league_prices

class PaymentAmountCalculationTest(TestCase):
    """Test payment amount calculations"""

    def test_calculate_payment_amounts_default_fee(self):
        """Test calculation with default 25% fee"""
        result = calculate_payment_amounts(
            gross_amount=Decimal('1000.00'),
            fee_percentage=Decimal('25.00')
        )

        self.assertEqual(result['platform_fee'], Decimal('250.00'))
        self.assertEqual(result['prize_pool'], Decimal('750.00'))

    def test_calculate_payment_amounts_custom_fee(self):
        """Test calculation with custom fee percentage"""
        result = calculate_payment_amounts(
            gross_amount=Decimal('500.00'),
            fee_percentage=Decimal('20.00')
        )

        self.assertEqual(result['platform_fee'], Decimal('100.00'))
        self.assertEqual(result['prize_pool'], Decimal('400.00'))


class CreateRoundPaymentTest(TestCase):
    """Test round payment creation"""

    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league, round_state=Round.NOT_STARTED_ROUND)
        self.config = PaidLeagueConfigFactory(
            league=self.league,
            is_paid_mode_enabled=True,
            round_price_ars=Decimal('500.00')
        )

    @patch('apps.payment.services.get_mercadopago_service')
    def test_create_round_payment_success(self, mock_mp_service):
        """Test successful round payment creation"""
        mock_service = MagicMock()
        mock_service.create_preference.return_value = {
            'preference_id': 'pref_123',
            'init_point': 'https://mercadopago.com/checkout/123',
            'sandbox_init_point': 'https://sandbox.mercadopago.com/checkout/123',
        }
        mock_mp_service.return_value = mock_service

        result = create_round_payment(self.user, self.round)

        self.assertIn('payment_id', result)
        self.assertIn('init_point', result)
        self.assertEqual(result['amount'], '500.00')

        payment = Payment.objects.get(id=result['payment_id'])
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.gross_amount_ars, Decimal('500.00'))

    def test_create_round_payment_disabled_mode(self):
        """Test payment fails when paid mode is disabled"""
        self.config.is_paid_mode_enabled = False
        self.config.save()

        result = create_round_payment(self.user, self.round)

        self.assertIn('error', result)
        self.assertEqual(result['error'], 'Paid mode is not enabled for this league')

    def test_create_round_payment_already_exists(self):
        """Test payment fails when user already has a bet for this round"""
        payment = PaymentFactory(user=self.user, league=self.league, round=self.round)
        PaidBetRoundFactory(user=self.user, round=self.round, payment=payment)

        result = create_round_payment(self.user, self.round)

        self.assertIn('error', result)
        self.assertEqual(result['error'], 'You already have a paid bet for this round')

    def test_create_round_payment_round_started(self):
        """Test payment fails when round has already started."""
        self.round.round_state = Round.PENDING_ROUND
        self.round.save()

        result = create_round_payment(self.user, self.round)

        self.assertIn('error', result)
        self.assertEqual(result['error'], 'This round is no longer available for betting')


class ProcessApprovedPaymentTest(TestCase):
    """Test approved payment processing"""

    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league, is_general_round=False)
        self.team_1 = TeamFactory()
        self.team_2 = TeamFactory()
        self.match_1 = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.match_2 = MatchFactory(round=self.round, team_1=self.team_2, team_2=self.team_1)

    def test_process_round_payment(self):
        """Test processing approved round payment creates bet records"""
        payment = PaymentFactory(
            user=self.user,
            league=self.league,
            round=self.round,
            payment_type=Payment.PAYMENT_TYPE_ROUND,
            status=Payment.STATUS_APPROVED,
        )

        result = process_approved_payment(payment)

        self.assertTrue(result)

        # Check PaidBetRound was created
        paid_bet_round = PaidBetRound.objects.filter(user=self.user, round=self.round).first()
        self.assertIsNotNone(paid_bet_round)

        # Check FREE mode BetRound was also created (auto-registration)
        bet_league = BetLeague.objects.filter(user=self.user, league=self.league).first()
        self.assertIsNotNone(bet_league)
        bet_round = BetRound.objects.filter(bet_league=bet_league, round=self.round).first()
        self.assertIsNotNone(bet_round)

        # Check MatchResult records were created and linked to PaidBetRound
        match_results = MatchResult.objects.filter(paid_bet_round=paid_bet_round)
        self.assertEqual(match_results.count(), 2)

        # Check prize pool was updated
        prize_pool = PaidPrizePool.objects.filter(round=self.round).first()
        self.assertIsNotNone(prize_pool)
        self.assertEqual(prize_pool.total_pool_ars, payment.prize_pool_ars)

    def test_process_non_approved_payment(self):
        """Test that non-approved payments are not processed"""
        payment = PaymentFactory(
            user=self.user,
            league=self.league,
            round=self.round,
            status=Payment.STATUS_PENDING,
        )

        result = process_approved_payment(payment)

        self.assertFalse(result)
        self.assertEqual(PaidBetRound.objects.count(), 0)


class PrizeDistributionTest(TestCase):
    """Test prize distribution"""

    def setUp(self):
        self.league = LeagueFactory()
        self.round = RoundFactory(
            league=self.league,
            round_state=Round.FINALIZED_ROUND,
            is_general_round=False
        )
        self.team_1 = TeamFactory()
        self.team_2 = TeamFactory()
        self.match = MatchFactory(
            round=self.round,
            team_1=self.team_1,
            team_2=self.team_2,
            match_state=Match.FINALIZED_MATCH
        )
        self.prize_pool = PaidPrizePoolFactory(
            league=self.league,
            round=self.round,
            total_pool_ars=Decimal('1000.00'),
            distributed=False
        )
        self.users = [AppUserFactory() for _ in range(3)]
        self.payments = []
        self.paid_bet_rounds = []

        for i, user in enumerate(self.users):
            # Create FREE mode structures
            bet_league = BetLeague.objects.create(user=user, league=self.league)
            bet_round = BetRound.objects.create(bet_league=bet_league, round=self.round)

            # Create payment and PaidBetRound
            payment = PaymentFactory(
                user=user, league=self.league, round=self.round
            )
            paid_bet_round = PaidBetRoundFactory(
                user=user, round=self.round, payment=payment
            )

            # Create MatchResult linked to both BetRound and PaidBetRound
            MatchResult.objects.create(
                bet_round=bet_round,
                paid_bet_round=paid_bet_round,
                match=self.match,
                goals_team_1=i,
                goals_team_2=0,
                points=3 - i,  # 3, 2, 1 points
                is_exact=(i == 0)
            )
            self.payments.append(payment)
            self.paid_bet_rounds.append(paid_bet_round)

    def test_distribute_round_prizes(self):
        """Test prize distribution to top 3 winners"""
        result = distribute_round_prizes(self.round)
        self.assertTrue(result)

        self.prize_pool.refresh_from_db()
        self.assertTrue(self.prize_pool.distributed)

        # Check winners were created
        winners = PaidWinner.objects.filter(prize_pool=self.prize_pool).order_by('position')
        self.assertEqual(winners.count(), 3)

        # Check prize amounts (60/25/15 split of 1000)
        self.assertEqual(winners[0].prize_amount_ars, Decimal('600.00'))
        self.assertEqual(winners[1].prize_amount_ars, Decimal('250.00'))
        self.assertEqual(winners[2].prize_amount_ars, Decimal('150.00'))

        # Check winner flags on paid bet rounds
        self.paid_bet_rounds[0].refresh_from_db()
        self.paid_bet_rounds[1].refresh_from_db()
        self.paid_bet_rounds[2].refresh_from_db()
        self.assertTrue(self.paid_bet_rounds[0].winner_first)
        self.assertTrue(self.paid_bet_rounds[1].winner_second)
        self.assertTrue(self.paid_bet_rounds[2].winner_third)


class PaymentAPITest(APITestCase):
    """Test payment API endpoints"""

    def setUp(self):
        self.user = AppUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            name='Test',
            last_name='User',
            password='testpass123'
        )
        self.league = LeagueFactory()
        self.round = RoundFactory(
            league=self.league,
            round_state=Round.NOT_STARTED_ROUND,
            is_general_round=False
        )
        self.config = PaidLeagueConfigFactory(
            league=self.league,
            is_paid_mode_enabled=True
        )
        self.client.force_authenticate(user=self.user)

    def test_list_paid_leagues(self):
        """Test listing leagues with paid mode enabled"""
        url = '/api/payments/leagues/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('apps.payment.services.get_mercadopago_service')
    def test_create_round_payment(self, mock_mp_service):
        """Test creating a round payment"""
        mock_service = MagicMock()
        mock_service.create_preference.return_value = {
            'preference_id': 'pref_123',
            'init_point': 'https://mercadopago.com/checkout/123',
        }
        mock_mp_service.return_value = mock_service

        url = f'/api/payments/round/{self.round.id}/pay/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('init_point', response.data)
        self.assertIn('payment_id', response.data)

    def test_payment_status(self):
        """Test checking payment status"""
        payment = PaymentFactory(user=self.user, league=self.league)

        url = f'/api/payments/status/{payment.external_reference}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['external_reference'], payment.external_reference)

    def test_payment_status_not_found(self):
        """Test payment status for non-existent payment"""
        url = '/api/payments/status/nonexistent/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_round_leaderboard(self):
        """Test round leaderboard endpoint"""
        payment = PaymentFactory(user=self.user, league=self.league, round=self.round)
        bet_round = PaidBetRoundFactory(user=self.user, round=self.round, payment=payment)

        url = f'/api/payments/leaderboard/round/{self.round.slug}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], self.user.username)


class PaidMatchResultUpdateTest(APITestCase):
    """Test updating match predictions"""

    def setUp(self):
        self.user = AppUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            name='Test',
            last_name='User',
            password='testpass123'
        )
        self.league = LeagueFactory()
        self.round = RoundFactory(
            league=self.league,
            round_state=Round.NOT_STARTED_ROUND
        )
        self.team_1 = TeamFactory()
        self.team_2 = TeamFactory()
        self.match = MatchFactory(
            round=self.round,
            team_1=self.team_1,
            team_2=self.team_2,
            match_state=Match.NOT_STARTED_MATCH
        )
        # Create FREE mode structures
        bet_league = BetLeague.objects.create(user=self.user, league=self.league)
        self.bet_round_free = BetRound.objects.create(bet_league=bet_league, round=self.round)

        # Create payment and PaidBetRound
        payment = PaymentFactory(user=self.user, league=self.league, round=self.round)
        self.paid_bet_round = PaidBetRoundFactory(
            user=self.user, round=self.round, payment=payment
        )

        # Create unified MatchResult linked to both
        self.match_result = MatchResult.objects.create(
            bet_round=self.bet_round_free,
            paid_bet_round=self.paid_bet_round,
            match=self.match,
        )
        self.client.force_authenticate(user=self.user)

    def test_update_prediction(self):
        """Test updating a match prediction"""
        url = f'/api/payments/predictions/{self.match_result.id}/'
        data = {'goals_team_1': 2, 'goals_team_2': 1}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.match_result.refresh_from_db()
        self.assertEqual(self.match_result.goals_team_1, 2)
        self.assertEqual(self.match_result.goals_team_2, 1)

    def test_update_prediction_after_match_started(self):
        """Test that predictions cannot be updated after match starts"""
        self.match.match_state = Match.PENDING_MATCH
        self.match.save()

        url = f'/api/payments/predictions/{self.match_result.id}/'
        data = {'goals_team_1': 2, 'goals_team_2': 1}
        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_predictions(self):
        """Test bulk updating predictions"""
        url = f'/api/payments/predictions/bulk/{self.paid_bet_round.id}/'
        data = {
            'predictions': [
                {'match_id': self.match.id, 'goals_team_1': 3, 'goals_team_2': 0}
            ]
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['updated']), 1)
        self.assertEqual(len(response.data['errors']), 0)


class CreateLeaguePaymentWithExistingRoundsTest(TestCase):
    """Test that league payment works when user has existing paid rounds"""

    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory()
        self.config = PaidLeagueConfigFactory(
            league=self.league,
            is_paid_mode_enabled=True,
            round_price_ars=Decimal('500.00'),
            league_price_ars=Decimal('2000.00'),
        )
        self.rounds = [
            RoundFactory(league=self.league, round_state=Round.NOT_STARTED_ROUND, is_general_round=False)
            for _ in range(4)
        ]

    @patch('apps.payment.services.get_mercadopago_service')
    def test_create_league_payment_with_existing_paid_rounds(self, mock_mp_service):
        """Test league payment succeeds even when user has existing paid rounds"""
        mock_service = MagicMock()
        mock_service.create_preference.return_value = {
            'preference_id': 'pref_123',
            'init_point': 'https://mercadopago.com/checkout/123',
            'sandbox_init_point': 'https://sandbox.mercadopago.com/checkout/123',
        }
        mock_mp_service.return_value = mock_service

        # User already paid for one round individually
        payment = PaymentFactory(user=self.user, league=self.league, round=self.rounds[0])
        PaidBetRoundFactory(user=self.user, round=self.rounds[0], payment=payment)

        result = create_league_payment(self.user, self.league)

        self.assertNotIn('error', result)
        self.assertIn('payment_id', result)

    def test_league_bet_records_skip_already_paid_rounds(self):
        """Test that _create_league_bet_records skips rounds the user already paid for"""
        from apps.payment.services import _create_league_bet_records

        # User already paid for round 0
        existing_payment = PaymentFactory(
            user=self.user, league=self.league, round=self.rounds[0],
            payment_type=Payment.PAYMENT_TYPE_ROUND, status=Payment.STATUS_APPROVED,
        )
        PaidBetRoundFactory(user=self.user, round=self.rounds[0], payment=existing_payment)

        # Now process a league payment
        league_payment = PaymentFactory(
            user=self.user, league=self.league, round=None,
            payment_type=Payment.PAYMENT_TYPE_LEAGUE, status=Payment.STATUS_APPROVED,
        )

        _create_league_bet_records(league_payment)

        # Should have PaidBetRound for all 4 rounds (1 existing + 3 new)
        paid_rounds = PaidBetRound.objects.filter(user=self.user, state=True)
        self.assertEqual(paid_rounds.count(), 4)

        # The existing one should still reference the original payment
        existing = PaidBetRound.objects.get(user=self.user, round=self.rounds[0])
        self.assertEqual(existing.payment, existing_payment)

        # The new ones should reference the league payment
        new_paid = PaidBetRound.objects.filter(user=self.user, payment=league_payment)
        self.assertEqual(new_paid.count(), 3)


class UpdateLeaguePricesTaskTest(TestCase):
    """Test the update_league_prices periodic task"""

    def test_updates_league_price_based_on_remaining_rounds(self):
        """Test price is recalculated as round_price * remaining * 0.85"""
        league = LeagueFactory()
        config = PaidLeagueConfigFactory(
            league=league,
            is_paid_mode_enabled=True,
            round_price_ars=Decimal('500.00'),
            league_price_ars=Decimal('9999.00'),
        )
        for _ in range(3):
            RoundFactory(
                league=league, round_state=Round.NOT_STARTED_ROUND, is_general_round=False
            )
        RoundFactory(league=league, round_state=Round.PENDING_ROUND, is_general_round=False)

        update_league_prices()

        config.refresh_from_db()
        # 500*3*0.85 = 1275.00
        self.assertEqual(config.league_price_ars, Decimal('1275.00'))

    def test_no_update_when_price_unchanged(self):
        """Test no save happens when price is already correct"""
        league = LeagueFactory()
        config = PaidLeagueConfigFactory(
            league=league,
            is_paid_mode_enabled=True,
            round_price_ars=Decimal('500.00'),
            league_price_ars=Decimal('850.00'),  # already correct for 2 rounds
        )
        for _ in range(2):
            RoundFactory(
                league=league, round_state=Round.NOT_STARTED_ROUND, is_general_round=False
            )

        update_league_prices()

        config.refresh_from_db()
        self.assertEqual(config.league_price_ars, Decimal('850.00'))


class WebhookSignatureVerificationTest(APITestCase):
    """Test MercadoPago webhook signature verification"""

    def setUp(self):
        self.url = '/api/payments/webhook/mercadopago/'

    @patch('apps.payment.views.django_settings')
    def test_webhook_rejected_without_signature(self, mock_settings):
        """Test webhook returns 403 when X-Signature header is missing"""
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = 'test_secret_key'

        response = self.client.post(self.url, data={'type': 'payment', 'data': {'id': '123'}})

        self.assertEqual(response.status_code, 403)

    @patch('apps.payment.views.django_settings')
    def test_webhook_rejected_with_invalid_signature(self, mock_settings):
        """Test webhook returns 403 with invalid signature"""
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = 'test_secret_key'

        response = self.client.post(
            self.url + '?data.id=123',
            data={'type': 'payment', 'data': {'id': '123'}},
            HTTP_X_SIGNATURE='ts=1234567890,v1=invalidsignature',
            HTTP_X_REQUEST_ID='req-123',
        )

        self.assertEqual(response.status_code, 403)

    @patch('apps.payment.views.django_settings')
    @patch('apps.payment.views.get_mercadopago_service')
    def test_webhook_accepted_with_valid_signature(self, mock_mp_service, mock_settings):
        """Test webhook processes request with valid signature"""
        import hashlib
        import hmac as hmac_mod

        secret = 'test_secret_key'
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = secret

        mock_service = MagicMock()
        mock_service.get_payment.return_value = {'status': 'pending', 'external_reference': 'sp_test123'}
        mock_mp_service.return_value = mock_service

        data_id = '12345'
        request_id = 'req-abc'
        ts = '1700000000'
        manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
        computed = hmac_mod.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

        response = self.client.post(
            self.url + f'?data.id={data_id}&topic=payment&id={data_id}',
            data={'type': 'payment', 'data': {'id': data_id}},
            HTTP_X_SIGNATURE=f'ts={ts},v1={computed}',
            HTTP_X_REQUEST_ID=request_id,
        )

        self.assertEqual(response.status_code, 200)

    @patch('apps.payment.views.django_settings')
    def test_webhook_allowed_when_secret_not_configured(self, mock_settings):
        """Test webhook is allowed when MERCADOPAGO_WEBHOOK_SECRET is empty (dev mode)"""
        mock_settings.MERCADOPAGO_WEBHOOK_SECRET = ''

        response = self.client.post(self.url, data={'type': 'test'})

        self.assertEqual(response.status_code, 200)


class WebhookAtomicProcessingTest(TestCase):
    """Test that webhook payment processing is atomic"""

    def setUp(self):
        self.user = AppUserFactory()
        self.league = LeagueFactory()
        self.round = RoundFactory(league=self.league, is_general_round=False)
        self.team_1 = TeamFactory()
        self.team_2 = TeamFactory()
        self.match = MatchFactory(round=self.round, team_1=self.team_1, team_2=self.team_2)
        self.config = PaidLeagueConfigFactory(
            league=self.league, is_paid_mode_enabled=True
        )

    @patch('apps.payment.services.get_mercadopago_service')
    def test_duplicate_webhook_does_not_double_process(self, mock_mp_service):
        """Test that calling update_payment_from_webhook twice only processes once"""
        mock_service = MagicMock()
        mock_service.get_payment.return_value = {
            'status': 'approved',
            'external_reference': None,
        }
        mock_mp_service.return_value = mock_service

        payment = PaymentFactory(
            user=self.user, league=self.league, round=self.round,
            payment_type=Payment.PAYMENT_TYPE_ROUND, status=Payment.STATUS_PENDING,
        )
        mock_service.get_payment.return_value['external_reference'] = payment.external_reference

        # First call should process
        result1 = update_payment_from_webhook(payment.external_reference, 'mp_pay_1')
        self.assertTrue(result1)

        # Second call should short-circuit (already approved)
        result2 = update_payment_from_webhook(payment.external_reference, 'mp_pay_1')
        self.assertTrue(result2)

        # Only 1 PaidBetRound should exist
        self.assertEqual(PaidBetRound.objects.filter(user=self.user, round=self.round).count(), 1)
