from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.match.utils import get_match_result_points
from apps.match.models import MatchResult, Match

class Command(BaseCommand):
    """Sums the points for the match results based on the match"""
    def add_arguments(self, parser):
        parser.add_argument('match_id', type=int)
    
    def handle(self, *args, **options):
        match_id = options['match_id']
        match = get_object_or_404(Match, id=match_id, state=True)
        match_results_count = 0
        original_match_result = get_object_or_404(MatchResult, 
            state=True, 
            match=match,
            original_result=True
        )
        user_match_results = MatchResult.objects.filter(
            state=True,
            match=match,
            original_result=False
        )

        with transaction.atomic(): 
            match_results_count += user_match_results.count()

            for match_result in user_match_results:
                match_result.points = get_match_result_points(
                    user_goals_team_1=match_result.goals_team_1,
                    user_goals_team_2=match_result.goals_team_2,
                    original_goals_team_1=original_match_result.goals_team_1,
                    original_goals_team_2=original_match_result.goals_team_2
                )
                match_result.save()
            match.match_state = Match.FINALIZED_MATCH
            match.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully updated "%s" match results' % match_results_count)
        )

        

 
