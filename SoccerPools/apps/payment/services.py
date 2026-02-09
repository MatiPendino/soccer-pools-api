import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, F
from django.utils import timezone
from django.core.mail import mail_admins
from apps.league.models import Round
from apps.match.models import Match, MatchResult
from apps.bet.models import BetLeague, BetRound
from .models import (
    PaidLeagueConfig, Payment, PaidBetRound, PaidPrizePool, PaidWinner,
)
from .mercadopago_service import get_mercadopago_service

logger = logging.getLogger(__name__)

# Prize distribution percentages
FIRST_PLACE_PERCENTAGE = Decimal('0.70')
SECOND_PLACE_PERCENTAGE = Decimal('0.20')
THIRD_PLACE_PERCENTAGE = Decimal('0.10')

def calculate_payment_amounts(gross_amount, fee_percentage):
    """Calculate platform fee and prize pool contribution"""
    fee_rate = fee_percentage / Decimal('100')
    platform_fee = gross_amount * fee_rate
    prize_pool = gross_amount - platform_fee

    return {
        'platform_fee': platform_fee.quantize(Decimal('0.01')),
        'prize_pool': prize_pool.quantize(Decimal('0.01')),
    }


def create_round_payment(user, round):
    """Create a payment for a single round bet"""
    league = round.league

    # Check if paid mode is enabled
    try:
        config = league.paid_config
        if not config.is_paid_mode_enabled:
            return {'error': 'Paid mode is not enabled for this league'}
    except PaidLeagueConfig.DoesNotExist:
        return {'error': 'Paid mode is not configured for this league'}

    # Check if user already has a paid bet for this round
    if PaidBetRound.objects.filter(user=user, round=round, state=True).exists():
        return {'error': 'You already have a paid bet for this round'}

    # Check if round is still open for betting
    if round.round_state != Round.NOT_STARTED_ROUND:
        return {'error': 'This round is no longer available for betting'}

    # Extra safety: check if round has already started based on time
    if round.start_date and round.start_date <= timezone.now():
        return {'error': 'This round has already started'}

    gross_amount = config.round_price_ars
    amounts = calculate_payment_amounts(gross_amount, config.platform_fee_percentage)

    payment = Payment.objects.create(
        user=user,
        payment_type=Payment.PAYMENT_TYPE_ROUND,
        gross_amount_ars=gross_amount,
        platform_fee_ars=amounts['platform_fee'],
        prize_pool_ars=amounts['prize_pool'],
        league=league,
        round=round,
    )

    # Create MercadoPago preference
    mp_service = get_mercadopago_service()
    preference = mp_service.create_preference(
        title=f'Apuesta Ronda: {round.name}',
        description=f'Apuesta para {round.name} en {league.name}',
        amount=gross_amount,
        external_reference=payment.external_reference,
        payer_email=user.email,
    )

    if 'error' in preference:
        payment.status = Payment.STATUS_CANCELLED
        payment.save()
        return {'error': preference['error']}

    payment.mp_preference_id = preference['preference_id']
    payment.save()

    logger.info(
        'Round payment created for user %s, round %s',
        user.username, round.name
    )

    return {
        'payment_id': payment.id,
        'external_reference': payment.external_reference,
        'init_point': preference['init_point'],
        'sandbox_init_point': preference.get('sandbox_init_point'),
        'amount': str(gross_amount),
    }


def create_league_payment(user, league):
    """Create a payment for full league bet (15% discount)"""
    # Check if paid mode is enabled
    try:
        config = league.paid_config
        if not config.is_paid_mode_enabled:
            return {'error': 'Paid mode is not enabled for this league'}
    except PaidLeagueConfig.DoesNotExist:
        return {'error': 'Paid mode is not configured for this league'}

    # Get rounds that are still open for betting
    available_rounds = Round.objects.filter(
        league=league,
        round_state=Round.NOT_STARTED_ROUND,
        state=True,
        is_general_round=False,
    )

    if not available_rounds.exists():
        return {'error': 'No rounds available for betting'}

    gross_amount = config.league_price_ars
    amounts = calculate_payment_amounts(gross_amount, config.platform_fee_percentage)

    payment = Payment.objects.create(
        user=user,
        payment_type=Payment.PAYMENT_TYPE_LEAGUE,
        gross_amount_ars=gross_amount,
        platform_fee_ars=amounts['platform_fee'],
        prize_pool_ars=amounts['prize_pool'],
        league=league,
        round=None,
    )

    # Create MercadoPago preference
    mp_service = get_mercadopago_service()
    preference = mp_service.create_preference(
        title=f'Apuesta Liga Completa: {league.name}',
        description=f'Apuesta para todas las rondas de {league.name}',
        amount=gross_amount,
        external_reference=payment.external_reference,
        payer_email=user.email,
    )

    if 'error' in preference:
        payment.status = Payment.STATUS_CANCELLED
        payment.save()
        return {'error': preference['error']}

    payment.mp_preference_id = preference['preference_id']
    payment.save()

    logger.info(
        'League payment created for user %s, league %s',
        user.username, league.name
    )

    return {
        'payment_id': payment.id,
        'external_reference': payment.external_reference,
        'init_point': preference['init_point'],
        'sandbox_init_point': preference.get('sandbox_init_point'),
        'amount': str(gross_amount),
        'rounds_count': available_rounds.count(),
    }


def process_approved_payment(payment):
    """
    Process an approved payment: create bet records and update prize pool
    """
    if payment.status != Payment.STATUS_APPROVED:
        logger.warning('Attempted to process non-approved payment %s', payment.id)
        return False

    try:
        with transaction.atomic():
            if payment.payment_type == Payment.PAYMENT_TYPE_ROUND:
                _create_round_bet_records(payment)
                _update_round_prize_pool(payment)
            else:
                _create_league_bet_records(payment)
                _update_league_prize_pool(payment)

        logger.info('Payment %s processed successfully', payment.id)
        return True

    except Exception as e:
        logger.exception('Error processing payment %s', payment.id)
        return False


def _create_round_bet_records(payment):
    """Create PaidBetRound and link MatchResult records (auto-register if needed)"""
    user = payment.user
    round_obj = payment.round
    league = payment.league

    # Ensure user has BetLeague (FREE mode registration)
    bet_league, _ = BetLeague.objects.get_or_create(
        user=user,
        league=league,
        defaults={'state': True}
    )

    # Ensure user has BetRound for this round
    bet_round, bet_round_created = BetRound.objects.get_or_create(
        bet_league=bet_league,
        round=round_obj,
        defaults={'state': True}
    )

    # If BetRound was just created, create MatchResult records
    if bet_round_created:
        matches = Match.objects.filter(round=round_obj, state=True)
        for match in matches:
            MatchResult.objects.create(
                bet_round=bet_round,
                match=match,
            )

    # Create PaidBetRound
    paid_bet_round = PaidBetRound.objects.create(
        user=user,
        round=round_obj,
        payment=payment
    )

    # Link all MatchResult records to PaidBetRound
    MatchResult.objects.filter(
        bet_round=bet_round,
        state=True
    ).update(paid_bet_round=paid_bet_round)

    logger.info(
        'Created PaidBetRound for user %s, round %s (auto-registered: %s)',
        user.username, round_obj.name, bet_round_created
    )


def _create_league_bet_records(payment):
    """Create PaidBetRound and link MatchResult records for all available rounds"""
    user = payment.user
    league = payment.league

    # Ensure user has BetLeague (FREE mode registration)
    bet_league, _ = BetLeague.objects.get_or_create(
        user=user,
        league=league,
        defaults={'state': True}
    )

    rounds = Round.objects.filter(
        league=league,
        round_state=Round.NOT_STARTED_ROUND,
        state=True,
        is_general_round=False,
    )

    # Skip rounds where user already has a PaidBetRound
    existing_paid_round_ids = set(
        PaidBetRound.objects.filter(
            user=user,
            round__in=rounds,
            state=True,
        ).values_list('round_id', flat=True)
    )

    auto_registered_count = 0
    for round_obj in rounds:
        if round_obj.id in existing_paid_round_ids:
            continue

        # Ensure user has BetRound for this round
        bet_round, bet_round_created = BetRound.objects.get_or_create(
            bet_league=bet_league,
            round=round_obj,
            defaults={'state': True}
        )

        # If BetRound was just created, create MatchResult records
        if bet_round_created:
            auto_registered_count += 1
            matches = Match.objects.filter(round=round_obj, state=True)
            for match in matches:
                MatchResult.objects.create(
                    bet_round=bet_round,
                    match=match,
                )

        # Create PaidBetRound
        paid_bet_round = PaidBetRound.objects.create(
            user=user,
            round=round_obj,
            payment=payment,
        )

        # Link all MatchResult records to PaidBetRound
        MatchResult.objects.filter(
            bet_round=bet_round,
            state=True
        ).update(paid_bet_round=paid_bet_round)

    logger.info(
        'Created PaidBetRounds for user %s in league %s (%d rounds, %d auto-registered)',
        user.username, league.name, rounds.count(), auto_registered_count
    )


def _update_round_prize_pool(payment):
    """Update the prize pool for a round"""
    prize_pool, created = PaidPrizePool.objects.get_or_create(
        league=payment.league,
        round=payment.round,
        is_league_pool=False,
        defaults={'total_pool_ars': Decimal('0')}
    )

    prize_pool.total_pool_ars = F('total_pool_ars') + payment.prize_pool_ars
    prize_pool.save()

    logger.info(
        'Updated round prize pool: %s now at $%s',
        payment.round.name, prize_pool.total_pool_ars
    )


def _update_league_prize_pool(payment):
    """Update the prize pool for a league"""
    rounds = Round.objects.filter(
        league=payment.league,
        round_state=Round.NOT_STARTED_ROUND,
        state=True,
        is_general_round=False,
    )

    rounds_count = rounds.count()
    if rounds_count == 0:
        return

    # Distribute pool contribution evenly across rounds
    per_round_contribution = payment.prize_pool_ars / rounds_count

    for round_obj in rounds:
        prize_pool, created = PaidPrizePool.objects.get_or_create(
            league=payment.league,
            round=round_obj,
            is_league_pool=False,
            defaults={'total_pool_ars': Decimal('0')}
        )

        prize_pool.total_pool_ars = F('total_pool_ars') + per_round_contribution
        prize_pool.save()

    logger.info(
        'Updated league prize pools for %s (%d rounds)',
        payment.league.name, rounds_count
    )


def distribute_round_prizes(round):
    """Distribute prizes for a finalized round"""
    try:
        prize_pool = PaidPrizePool.objects.filter(
            round=round,
            is_league_pool=False,
            distributed=False,
            state=True,
        ).first()

        if not prize_pool:
            logger.info('No undistributed prize pool for round %s', round.name)
            return True

        if prize_pool.total_pool_ars <= 0:
            prize_pool.distributed = True
            prize_pool.save()
            return True

        paid_bet_rounds = PaidBetRound.objects.filter(
            round=round,
            state=True,
        )

        # Calculate points for each bet using MatchResult
        bet_points = []
        for bet in paid_bet_rounds:
            points = MatchResult.objects.filter(
                paid_bet_round=bet,
                state=True
            ).aggregate(total=Sum('points'))['total'] or 0
            bet_points.append((bet, points))

        # Sort by points descending
        bet_points.sort(key=lambda x: x[1], reverse=True)

        if len(bet_points) < 3:
            logger.warning(
                'Not enough participants for round %s (need 3, have %d)',
                round.name, len(bet_points)
            )
            return False

        with transaction.atomic():
            # Calculate prize amounts
            total = prize_pool.total_pool_ars
            first_prize = total * FIRST_PLACE_PERCENTAGE
            second_prize = total * SECOND_PLACE_PERCENTAGE
            third_prize = total * THIRD_PLACE_PERCENTAGE

            # Create winner records
            winners_data = [
                (bet_points[0][0], 1, first_prize),
                (bet_points[1][0], 2, second_prize),
                (bet_points[2][0], 3, third_prize),
            ]

            for bet, position, prize in winners_data:
                bet_round = bet
                if position == 1:
                    bet_round.winner_first = True
                elif position == 2:
                    bet_round.winner_second = True
                else:
                    bet_round.winner_third = True
                bet_round.save()

                PaidWinner.objects.create(
                    user=bet.user,
                    prize_pool=prize_pool,
                    position=position,
                    prize_amount_ars=prize.quantize(Decimal('0.01')),
                )

            prize_pool.distributed = True
            prize_pool.save()

            _notify_admins_of_winners(round, winners_data)

        logger.info('Distributed prizes for round %s', round.name)
        return True

    except Exception as e:
        logger.exception('Error distributing prizes for round %s', round.name)
        return False


def _notify_admins_of_winners(round, winners_data):
    """Send email notification to admins about winners"""
    subject = f'[Soccer Pools] Winners for {round.name}'

    message_lines = [
        f'Round: {round.name}',
        f'League: {round.league.name}',
        'Winners:',
    ]

    for bet, position, prize in winners_data:
        position_name = {1: '1st', 2: '2nd', 3: '3rd'}.get(position)
        message_lines.append(
            f'{position_name}: {bet.user.username} ({bet.user.email}) - ${prize:.2f}'
        )

    message_lines.extend([
        'Please contact the winners to arrange payment.',
        'You can mark them as contacted/paid in the admin panel.',
    ])

    mail_admins(subject, '\n'.join(message_lines))


def get_payment_by_reference(external_reference):
    return Payment.objects.filter(external_reference=external_reference).first()


def update_payment_from_webhook(external_reference, mp_payment_id):
    """Update payment status from MercadoPago webhook"""
    # Fetch MP payment details outside the lock to minimize lock duration
    mp_service = get_mercadopago_service()
    mp_payment = mp_service.get_payment(mp_payment_id)

    if 'error' in mp_payment:
        logger.error('Error fetching MP payment: %s', mp_payment['error'])
        return False

    mp_status = mp_payment.get('status')

    status_mapping = {
        'approved': Payment.STATUS_APPROVED,
        'pending': Payment.STATUS_PENDING,
        'rejected': Payment.STATUS_REJECTED,
        'cancelled': Payment.STATUS_CANCELLED,
        'refunded': Payment.STATUS_REFUNDED,
    }
    new_status = status_mapping.get(mp_status, Payment.STATUS_PENDING)

    with transaction.atomic():
        payment = (
            Payment.objects
            .select_for_update()
            .filter(external_reference=external_reference)
            .first()
        )

        if not payment:
            logger.warning('Payment not found for reference: %s', external_reference)
            return False

        if payment.status == Payment.STATUS_APPROVED:
            logger.info('Payment %s already approved', payment.id)
            return True

        payment.mp_payment_id = mp_payment_id
        payment.status = new_status
        payment.save()

        if payment.status == Payment.STATUS_APPROVED:
            return process_approved_payment(payment)

    return False
