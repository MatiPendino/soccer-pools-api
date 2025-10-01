from django.db.models import F
from apps.bet.models import BetRound
from apps.app_user.models import CoinGrant
from apps.bet.services import update_top_three_bet_league_winners
from apps.notification.utils import send_push_winner
from .utils import get_coins_prizes

def give_referral_earnings(referee_user, prize, competition_name):
    if referee_user.referred_by:
        referee_user.referred_by.coins = (
            F('coins') + int(prize * CoinGrant.REFERRER_EARNINGS_MULTIPLIER)
        )
        CoinGrant.objects.create(
            user=referee_user.referred_by,
            amount=int(prize * CoinGrant.REFERRER_EARNINGS_MULTIPLIER),
            reward_type=CoinGrant.REFERRAL_EARNED,
            description=f'Earned coins from referral for {referee_user.username} winning {competition_name}',
        )
        referee_user.referred_by.save(update_fields=['coins'])
        

def update_round_winners_prizes(round):
    """
        Update the winners of the round and distribute coins to the winners.
    """
    competition_name = round.name

    # Get the first three bet rounds of the round
    first_bet_round, second_bet_round, third_bet_round = BetRound.objects.with_matches_points(
        round_slug=round.slug
    )[:3]

    # Get the first three users of the bet rounds
    first_user = first_bet_round.get_user()
    second_user = second_bet_round.get_user()
    third_user = third_bet_round.get_user()

    # Update the winners of the bet rounds
    first_bet_round.winner_first = True
    second_bet_round.winner_second = True
    third_bet_round.winner_third = True
    first_bet_round.save(update_fields=['winner_first'])
    second_bet_round.save(update_fields=['winner_second'])
    third_bet_round.save(update_fields=['winner_third'])

    # If the round is a league, update the winners of the bet leagues too
    if round.is_general_round:
        update_top_three_bet_league_winners(
            league=round.league, first_user=first_user, second_user=second_user, third_user=third_user
        )

    # Distribute coins to the winners
    first_prize, second_prize, third_prize = get_coins_prizes(round)
    first_user.coins = F('coins') + first_prize
    second_user.coins = F('coins') + second_prize
    third_user.coins = F('coins') + third_prize
    first_user.save(update_fields=['coins'])
    second_user.save(update_fields=['coins'])
    third_user.save(update_fields=['coins'])

    # Distribute coins to the referrers
    give_referral_earnings(first_user, first_prize, round.name)
    give_referral_earnings(second_user, second_prize, round.name)
    give_referral_earnings(third_user, third_prize, round.name)

    # Send push notifications to the winners
    send_push_winner(first_user, competition_name, first_prize)
    send_push_winner(second_user, competition_name, second_prize)
    send_push_winner(third_user, competition_name, third_prize)