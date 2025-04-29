from .models import BetLeague

def update_top_three_bet_league_winners(league, first_user, second_user, third_user):
    first_bet_league = BetLeague.objects.filter(
        league=league, user=first_user
    ).first()
    second_bet_league = BetLeague.objects.filter(
        league=league, user=second_user
    ).first()
    third_bet_league = BetLeague.objects.filter(
        league=league, user=third_user
    ).first()

    first_bet_league.winner_first = True
    second_bet_league.winner_second = True
    third_bet_league.winner_third = True
    first_bet_league.save()
    second_bet_league.save()
    third_bet_league.save()