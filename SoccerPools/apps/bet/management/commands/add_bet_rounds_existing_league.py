from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League

class Command(BaseCommand):
    """Add bet rounds to an existing league"""
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int, help='League ID')

    def handle(self, *args, **options):
        # Get the league and its rounds
        league_id = options.get('league_id')
        league = get_object_or_404(League, state=True, api_league_id=league_id)
        rounds = league.rounds.all()

        # If there is no bet leagues or rounds, we do not need to create bet rounds
        if league.bet_leagues.count() == 0:
            print(f'No bet leagues found for league ID {league_id}.')
            return
        
        if rounds.count() == 0:
            print(f'No rounds found for league ID {league_id}.')
            return
        
        n_bet_rounds_created = 0
        for round in rounds:
            bet_rounds = round.bet_rounds.all()
            # Check if bet rounds already exist for the round
            # If there is no bet rounds it means a new round was added, so we create the bet rounds
            if bet_rounds.count() == 0:
                print(f'Creating bet rounds for league ID {league_id} and round {round.name}.')
                for bet_league in league.bet_leagues.all():
                    bet_round = round.bet_rounds.create(bet_league=bet_league, round=round)
                    print(f'Bet round created: {bet_round}')
                    n_bet_rounds_created += 1
            else:
                print(f'Bet rounds already exist for league ID {league_id} and round {round.name}.')

        print(f'{n_bet_rounds_created} bet rounds created for league ID {league_id}.')
        

