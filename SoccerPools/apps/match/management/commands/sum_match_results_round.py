from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.league.models import Round
from apps.match.utils import get_match_result_points
from apps.match.models import MatchResult, Match

class Command(BaseCommand):
    """Sums the points for the match results based on the round"""
    def add_arguments(self, parser):
        parser.add_argument('round_id', type=int)
    
    def handle(self, *args, **options):
        round_id = options['round_id']
        round = get_object_or_404(Round, state=True, id=round_id)
        matches = Match.objects.filter(
            state=True,
            round=round
        )
        match_results_count = 0

        with transaction.atomic():
            for match_i in matches:
                original_match_result = get_object_or_404(MatchResult, 
                    state=True, 
                    match=match_i,
                    original_result=True
                )
                user_match_results = MatchResult.objects.filter(
                    state=True,
                    match=match_i,
                    original_result=False
                )
                match_results_count += user_match_results.count()

                for match_result in user_match_results:
                    match_result.points = get_match_result_points(
                        user_goals_team_1=match_result.goals_team_1,
                        user_goals_team_2=match_result.goals_team_2,
                        original_goals_team_1=original_match_result.goals_team_1,
                        original_goals_team_2=original_match_result.goals_team_2
                    )
                    match_result.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully updated "%s" match results' % match_results_count)
        )

        

 
