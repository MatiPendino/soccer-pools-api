import hashlib
import hmac
import logging
from django.conf import settings as django_settings
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.league.models import League, Round
from apps.match.models import Match
from apps.match.models import MatchResult
from .mercadopago_service import get_mercadopago_service
from .models import PaidLeagueConfig, Payment, PaidBetRound, PaidPrizePool
from .serializers import (
    PaidLeagueConfigSerializer, PaymentSerializer, PaymentStatusSerializer,
    PaymentPreferenceResponseSerializer, PaidBetRoundDetailSerializer, PaidMatchResultSerializer,
    PaidMatchResultUpdateSerializer, PaidPrizePoolSerializer, LeaderboardEntrySerializer,
)
from .services import (
    create_round_payment, create_league_payment, get_payment_by_reference,
    update_payment_from_webhook,
)

logger = logging.getLogger(__name__)

class PaidLeagueListView(generics.ListAPIView):
    """List leagues that have paid mode enabled"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaidLeagueConfigSerializer

    def get_queryset(self):
        return PaidLeagueConfig.objects.filter(
            is_paid_mode_enabled=True,
            state=True,
            league__state=True,
        ).select_related('league')


class CreateRoundPaymentView(APIView):
    """Create a payment preference for a single round bet"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, round_id):
        round_obj = get_object_or_404(Round, id=round_id, state=True)
        result = create_round_payment(request.user, round_obj)

        if 'error' in result:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PaymentPreferenceResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateLeaguePaymentView(APIView):
    """Create a payment preference for full league bet (15% discount)"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, league_slug):
        league = get_object_or_404(League, slug=league_slug, state=True)
        result = create_league_payment(request.user, league)

        if 'error' in result:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PaymentPreferenceResponseSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PaymentStatusView(APIView):
    """Check payment status by external reference"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, external_ref):
        payment = get_payment_by_reference(external_ref)

        if not payment:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ensure user can only see their own payments
        if payment.user != request.user:
            return Response(
                {'error': 'Payment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)


class MercadoPagoWebhookView(APIView):
    """Handle MercadoPago IPN webhook notifications"""
    permission_classes = [permissions.AllowAny]

    def _verify_signature(self, request):
        """Verify MercadoPago webhook signature using HMAC-SHA256"""
        secret = django_settings.MERCADOPAGO_WEBHOOK_SECRET
        if not secret:
            logger.warning('MERCADOPAGO_WEBHOOK_SECRET not configured, skipping verification')
            return True

        x_signature = request.headers.get('X-Signature', '')
        x_request_id = request.headers.get('X-Request-Id', '')

        if not x_signature:
            logger.warning('Webhook missing X-Signature header')
            return False

        # Parse ts and v1 from X-Signature header (format: "ts=...,v1=...")
        parts = {}
        for part in x_signature.split(','):
            key_value = part.strip().split('=', 1)
            if len(key_value) == 2:
                parts[key_value[0].strip()] = key_value[1].strip()

        ts = parts.get('ts')
        received_hash = parts.get('v1')

        if not ts or not received_hash:
            logger.warning('Webhook X-Signature missing ts or v1')
            return False

        # Build the manifest string per MercadoPago docs
        data_id = request.query_params.get('data.id', '')
        manifest = f'id:{data_id};request-id:{x_request_id};ts:{ts};'

        # Compute HMAC-SHA256
        computed_hash = hmac.new(
            secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            logger.warning('Webhook signature verification failed')
            return False

        return True

    def post(self, request):
        if not self._verify_signature(request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get webhook data
        topic = request.query_params.get('topic') or request.data.get('type')
        resource_id = request.query_params.get('id') or request.data.get('data', {}).get('id')

        logger.info('MercadoPago webhook received: topic=%s, id=%s', topic, resource_id)

        if topic == 'payment' and resource_id:
            # Get payment details from MercadoPago
            mp_service = get_mercadopago_service()
            mp_payment = mp_service.get_payment(str(resource_id))

            if 'error' not in mp_payment:
                external_ref = mp_payment.get('external_reference')
                if external_ref:
                    update_payment_from_webhook(external_ref, str(resource_id))

        return Response(status=status.HTTP_200_OK)


class UserPaymentHistoryView(generics.ListAPIView):
    """List user payment history"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user,
            state=True,
        ).select_related('league', 'round').order_by('-creation_date')


class UserPaidBetRoundsView(generics.ListAPIView):
    """List user paid bet rounds"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaidBetRoundDetailSerializer

    def get_queryset(self):
        return PaidBetRound.objects.filter(
            user=self.request.user,
            state=True,
        ).select_related('round', 'payment').prefetch_related(
            'match_results__match__team_1',
            'match_results__match__team_2',
        )


class PaidBetRoundDetailView(generics.RetrieveAPIView):
    """Get details of a specific paid bet round"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaidBetRoundDetailSerializer

    def get_queryset(self):
        return PaidBetRound.objects.filter(
            user=self.request.user,
            state=True,
        ).prefetch_related(
            'match_results__match__team_1',
            'match_results__match__team_2',
        )


class UpdatePaidMatchResultView(APIView):
    """Update a match prediction (uses MatchResult)"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, match_result_id):
        match_result = get_object_or_404(
            MatchResult, id=match_result_id, paid_bet_round__user=request.user, state=True,
        )

        serializer = PaidMatchResultUpdateSerializer(
            match_result, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(PaidMatchResultSerializer(match_result).data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class BulkUpdatePaidMatchResultsView(APIView):
    """Update multiple match predictions at once (uses MatchResult)"""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, paid_bet_round_id):
        paid_bet_round = get_object_or_404(
            PaidBetRound, id=paid_bet_round_id, user=request.user, state=True,
        )

        # Check if round has started
        if paid_bet_round.round.round_state != Round.NOT_STARTED_ROUND:
            return Response(
                {'error': 'Cannot update predictions after round has started'},
                status=status.HTTP_400_BAD_REQUEST
            )

        predictions = request.data.get('predictions', [])
        if not predictions:
            return Response(
                {'error': 'No predictions provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_results = []
        errors = []

        for pred in predictions:
            match_id = pred.get('match_id')
            goals_team_1 = pred.get('goals_team_1')
            goals_team_2 = pred.get('goals_team_2')

            try:
                match_result = MatchResult.objects.get(
                    paid_bet_round=paid_bet_round,
                    match_id=match_id,
                    state=True,
                )

                # Check if match has started
                if match_result.match.match_state != Match.NOT_STARTED_MATCH:
                    errors.append({
                        'match_id': match_id,
                        'error': 'Match has already started'
                    })
                    continue

                match_result.goals_team_1 = goals_team_1
                match_result.goals_team_2 = goals_team_2
                match_result.save()
                updated_results.append(match_result)

            except MatchResult.DoesNotExist:
                errors.append({
                    'match_id': match_id,
                    'error': 'Match result not found'
                })

        response_data = {
            'updated': PaidMatchResultSerializer(updated_results, many=True).data,
            'errors': errors,
        }

        return Response(response_data)


class RoundLeaderboardView(APIView):
    """Get leaderboard for a paid round"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, round_slug):
        round_obj = get_object_or_404(Round, slug=round_slug, state=True)

        bet_rounds = PaidBetRound.objects.filter(
            round=round_obj,
            state=True,
        ).select_related('user')

        # Calculate points for each bet round using MatchResult
        leaderboard = []
        for bet_round in bet_rounds:
            results = MatchResult.objects.filter(
                paid_bet_round=bet_round,
                state=True
            ).aggregate(
                total_points=Sum('points'),
            )

            exact_count = MatchResult.objects.filter(
                paid_bet_round=bet_round,
                is_exact=True,
                state=True
            ).count()

            leaderboard.append({
                'username': bet_round.user.username,
                'profile_image': bet_round.user.profile_image.url if bet_round.user.profile_image else None,
                'points': results['total_points'] or 0,
                'exact_results': exact_count,
                'winner_first': bet_round.winner_first,
                'winner_second': bet_round.winner_second,
                'winner_third': bet_round.winner_third,
            })

        # Sort by points descending, then by exact results
        leaderboard.sort(key=lambda x: (-x['points'], -x['exact_results']))

        # Add rank
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i+1

        serializer = LeaderboardEntrySerializer(leaderboard, many=True)
        return Response(serializer.data)


class LeagueLeaderboardView(APIView):
    """Get aggregated leaderboard for a paid league"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, league_slug):
        league = get_object_or_404(League, slug=league_slug, state=True)
        bet_rounds = PaidBetRound.objects.filter(
            round__league=league,
            state=True,
        ).select_related('user', 'round')

        # Aggregate points per user using MatchResult
        user_stats = {}
        for bet_round in bet_rounds:
            user_id = bet_round.user.id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'username': bet_round.user.username,
                    'profile_image': bet_round.user.profile_image.url if bet_round.user.profile_image else None,
                    'points': 0,
                    'exact_results': 0,
                    'winner_first': False,
                    'winner_second': False,
                    'winner_third': False,
                }

            points = MatchResult.objects.filter(
                paid_bet_round=bet_round,
                state=True
            ).aggregate(total=Sum('points'))['total'] or 0

            exact_results = MatchResult.objects.filter(
                paid_bet_round=bet_round,
                is_exact=True,
                state=True
            ).count()

            user_stats[user_id]['points'] += points
            user_stats[user_id]['exact_results'] += exact_results

        # Convert to list and sort
        leaderboard = list(user_stats.values())
        leaderboard.sort(key=lambda x: (-x['points'], -x['exact_results']))

        # Add rank
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i+1

        serializer = LeaderboardEntrySerializer(leaderboard, many=True)
        return Response(serializer.data)


class RoundPrizePoolView(APIView):
    """Get prize pool info for a round"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, round_slug):
        round_obj = get_object_or_404(Round, slug=round_slug, state=True)

        prize_pool = PaidPrizePool.objects.filter(
            round=round_obj,
            is_league_pool=False,
            state=True,
        ).first()

        if not prize_pool:
            return Response({
                'total_pool_ars': '0.00',
                'distributed': False,
                'participants_count': 0,
            })

        participants_count = PaidBetRound.objects.filter(
            round=round_obj,
            state=True,
        ).count()

        data = PaidPrizePoolSerializer(prize_pool).data
        data['participants_count'] = participants_count

        return Response(data)
