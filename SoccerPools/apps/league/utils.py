
def get_coins_prize_player_based(bet_rounds_count, is_general_round, round_multiplier, league_multiplier):
    """
        Calculate the coins prize based on the number of bet rounds and if it is a general round or not
    """
    return bet_rounds_count * (
        round_multiplier if not is_general_round else league_multiplier
    )

def get_coins_prizes(round):
    """
        Get the coins prizes for first, second and third place based on the number of bet rounds
        and if it is a general round or not
    """
    from .models import Round, League

    n_bet_rounds = round.bet_rounds.count()
    prize_first_player_based = get_coins_prize_player_based(
        n_bet_rounds, round.is_general_round, Round.COINS_FIRST_PRIZE_MULT, League.COINS_FIRST_PRIZE_MULT
    )
    prize_second_player_based = get_coins_prize_player_based(
        n_bet_rounds, round.is_general_round, Round.COINS_SECOND_PRIZE_MULT, League.COINS_SECOND_PRIZE_MULT
    )
    prize_third_player_based = get_coins_prize_player_based(
        n_bet_rounds, round.is_general_round, Round.COINS_THIRD_PRIZE_MULT, League.COINS_THIRD_PRIZE_MULT
    )

    league_min_first, league_min_second, league_min_third = round.get_league_minimum_prizes()
    if round.is_general_round:
        first_prize = max(prize_first_player_based, league_min_first)
        second_prize = max(prize_second_player_based, league_min_second)
        third_prize = max(prize_third_player_based, league_min_third)
    else:
        first_prize = max(prize_first_player_based, round.minimum_coins_first_prize)
        second_prize = max(prize_second_player_based, round.minimum_coins_second_prize)
        third_prize = max(prize_third_player_based, round.minimum_coins_third_prize)

    return first_prize, second_prize, third_prize