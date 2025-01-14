from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from apps.league.models import Round
from apps.bet.models import Bet

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('round_id', type=int)

    def handle(self, *args, **options):
        round_id = options.get('round_id')
        round = get_object_or_404(Round, state=True, id=round_id)

        bets = Bet.objects.filter(
            state=True,
            round=round
        ).annotate(
            matches_points=Sum('match_result__points')
        )

        winner_bet = bets.order_by('-matches_points').first()
        winner_bet.winner = True
        winner_bet.save()

        self.stdout.write('Winner bet %s' % winner_bet)