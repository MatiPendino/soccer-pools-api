
def get_coins_prize_player_based(bet_rounds_count, is_general_round, round_multiplier, league_multiplier):
    """
        Calculate the coins prize based on the number of bet rounds and if it is a general round or not
    """
    return bet_rounds_count * (
        round_multiplier if not is_general_round else league_multiplier
    )
