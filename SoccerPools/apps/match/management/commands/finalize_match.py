from sentry_sdk import capture_message
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from django.db import transaction
from apps.match.utils import get_match_result_points
from apps.match.models import MatchResult, Match
from apps.notification.utils import send_push_nots_match


class Command(BaseCommand):
    """Command to manually finalize a match and update all match results"""
    def add_arguments(self, parser):
        parser.add_argument('match_id', type=int)
    
    def handle(self, *args, **options):
        # Get the Match based on the match_id provided
        match_id = options['match_id']
        match = get_object_or_404(Match, id=match_id, state=True)

        # Get the original match result and all user match results
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

        try:
            # Send push notifications to inform about the finalized match
            send_push_nots_match(
                team_1_name=match.team_1.name, 
                team_2_name=match.team_2.name, 
                goals_home=original_match_result.goals_team_1, 
                goals_away=original_match_result.goals_team_2, 
                league=match.round.league
            )
        except Exception as err:
            capture_message(f'Error sending push nots: {str(err)}', level="error")

        match_results_count = 0
        with transaction.atomic(): 
            match_results_count += user_match_results.count()

            # Update the points for each user match result
            for match_result in user_match_results:
                match_result.points = get_match_result_points(
                    user_goals_team_1=match_result.goals_team_1,
                    user_goals_team_2=match_result.goals_team_2,
                    original_goals_team_1=original_match_result.goals_team_1,
                    original_goals_team_2=original_match_result.goals_team_2
                )
            MatchResult.objects.bulk_update(user_match_results, ['points'])

            # Update the match state to FINALIZED_MATCH
            match.match_state = Match.FINALIZED_MATCH
            match.save()

        self.stdout.write(
            self.style.SUCCESS('Successfully updated "%s" match results' % match_results_count)
        )

        

 
