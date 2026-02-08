import logging
from decimal import Decimal
from celery import shared_task
from apps.league.models import Round
from .models import PaidLeagueConfig, PaidPrizePool
from .services import distribute_round_prizes

logger = logging.getLogger(__name__)

@shared_task
def finalize_paid_round_prizes(round_id):
    """
    Finalize a round and distribute prizes to winners

    Note: This task should be called when a round is fully finalized
    """
    try:
        round_obj = Round.objects.get(id=round_id)
    except Round.DoesNotExist:
        logger.error('Round %s not found', round_id)
        return

    # Verify round is finalized
    if round_obj.round_state != Round.FINALIZED_ROUND:
        logger.warning(
            'Round %s is not finalized yet (state=%s)',
            round_obj.name, round_obj.round_state
        )
        return

    # Check if there's a paid prize pool for this round
    prize_pool = PaidPrizePool.objects.filter(
        round=round_obj,
        is_league_pool=False,
        distributed=False,
        state=True,
    ).first()

    if not prize_pool:
        logger.info('No undistributed prize pool for round %s', round_obj.name)
        return

    # Distribute prizes
    success = distribute_round_prizes(round_obj)

    if success:
        logger.info('Successfully distributed prizes for round %s', round_obj.name)
    else:
        logger.error('Failed to distribute prizes for round %s', round_obj.name)


@shared_task
def check_paid_rounds_for_finalization():
    """Periodic task to check if any paid rounds need prize distribution"""
    # Get finalized rounds with undistributed prize pools
    undistributed_pools = PaidPrizePool.objects.filter(
        distributed=False,
        is_league_pool=False,
        state=True,
        round__round_state=Round.FINALIZED_ROUND,
    ).select_related('round')

    for pool in undistributed_pools:
        logger.info(
            'Found undistributed pool for round %s, triggering distribution',
            pool.round.name
        )
        finalize_paid_round_prizes.delay(pool.round.id)


@shared_task
def update_league_prices():
    """
    Periodic task to update league_price_ars based on remaining NOT_STARTED rounds
    """
    configs = PaidLeagueConfig.objects.filter(is_paid_mode_enabled=True, state=True)

    for config in configs:
        remaining_rounds = Round.objects.filter(
            league=config.league,
            round_state=Round.NOT_STARTED_ROUND,
            state=True,
            is_general_round=False,
        ).count()

        new_price = (
            config.round_price_ars * remaining_rounds * Decimal('0.85')
        ).quantize(Decimal('0.01'))

        if config.league_price_ars != new_price:
            config.league_price_ars = new_price
            config.save()
            logger.info(
                'Updated league price for %s: $%s (%d rounds)',
                config.league.name, new_price, remaining_rounds
            )
