from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.league.models import League
from apps.match.models import Match, MatchResult
from apps.notification.utils import send_push_new_round_available

class Command(BaseCommand):
    """Add match results to an existing league"""
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
        
        n_match_results_created = 0
        for round in rounds:
            matches = round.matches.all()
            if matches.count() == 0:
                print(f'No matches found for league ID {league_id} and round {round.name}.')
                continue
            
            match_results_count = 0
            for match in matches:
                match_results = match.match_results.all()
                # Check if the match results exist for this match
                # If there is no match results it means a new match was added, so we create the match 
                match_results_count = match_results.count()
                if match_results_count == 0:
                    bet_rounds = round.bet_rounds.all()
                    for bet_round in bet_rounds:
                        print(f'Creating match results for round {round.name}, and match {match}')
                        match_result = MatchResult.objects.create(
                            match=match,
                            bet_round=bet_round,
                        )
                        print(f'Match result created: {match_result}')
                        n_match_results_created += 1
                
            if match_results_count == 0:
                send_push_new_round_available(round.name, league)

        print(f'{n_match_results_created} match results created for league ID {league_id}')