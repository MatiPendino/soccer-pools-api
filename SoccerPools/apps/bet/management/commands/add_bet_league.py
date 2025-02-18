from django.core.management.base import BaseCommand
from apps.bet.models import BetRound, BetLeague

class Command(BaseCommand):
    def handle(self, *args, **options):
        bet_rounds = BetRound.objects.filter(state=True)
        for bet_round in bet_rounds:
            bet_league, was_created = BetLeague.objects.get_or_create(
                user=bet_round.user, 
                state=True,
                league=bet_round.round.league,
                defaults={
                    'is_last_visited_league': True
                }
            )
            bet_round.bet_league = bet_league
            bet_round.save()
        self.stdout.write('%s bet rounds updated' % bet_rounds.count())