from celery import shared_task
from django.utils.timezone import now, timedelta
from django.db import transaction
from django.db.models import Q, Count, F
from apps.match.models import Match
from apps.bet.models import BetRound
from apps.notification.utils import send_push_nots_round_winner
from .models import Round

@shared_task
def check_upcoming_rounds():
    """
        Check if any round start_date is within 20 minutes but hasn't started yet and 
        sets its state to pending
    """
    start_time = now() + timedelta(minutes=20)
    rounds = Round.objects.filter(state=True, start_date__gte=now(), start_date__lte=start_time)
    
    for round in rounds:
        round.round_state = Round.PENDING_ROUND
        round.save()


@shared_task
def finalize_pending_rounds():
    """Finalize all PENDING rounds where all its matches are FINALIZED, and distribute Coin Rewards"""

    pending_rounds = Round.objects.annotate(
        non_finalized_matches=Count(
            'matches',
            filter=Q(
                matches__match_state__in=[Match.NOT_STARTED_MATCH, Match.PENDING_MATCH], 
                matches__state=True
            )
        )
    ).filter(state=True, round_state=Round.PENDING_ROUND, non_finalized_matches=0)

    with transaction.atomic():
        for pending_round in pending_rounds:
            first_bet_round, second_bet_round, third_bet_round = BetRound.objects.with_matches_points(
                round_slug=pending_round.slug
            )[:3]

            first_bet_round.winner_first = True
            second_bet_round.winner_second = True
            third_bet_round.winner_third = True
            first_bet_round.save()
            second_bet_round.save()
            third_bet_round.save()

            n_bet_rounds = pending_round.bet_rounds.count()
            first_user = first_bet_round.get_user()
            second_user = second_bet_round.get_user()
            third_user = third_bet_round.get_user()

            first_prize = n_bet_rounds * Round.COINS_FIRST_PRIZE_MULT
            second_prize = n_bet_rounds * Round.COINS_SECOND_PRIZE_MULT
            third_prize = n_bet_rounds * Round.COINS_THIRD_PRIZE_MULT

            first_user.coins = F('coins') + first_prize
            second_user.coins = F('coins') + second_prize
            third_user.coins = F('coins') + third_prize
            first_user.save()
            second_user.save()
            third_user.save()
            
            send_push_nots_round_winner(first_user, pending_round.name, first_prize)
            send_push_nots_round_winner(second_user, pending_round.name, second_prize)
            send_push_nots_round_winner(third_user, pending_round.name, third_prize)
            
            
        pending_rounds.update(round_state=Round.FINALIZED_ROUND)