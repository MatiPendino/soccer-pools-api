from celery import shared_task
from decouple import config
from sentry_sdk import capture_message
from dateutil import parser
import requests
import json
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.utils.timezone import localtime
from apps.notification.utils import send_push_nots_match
from apps.league.models import Round
from apps.match.models import Match, MatchResult
from apps.match.utils import get_match_result_points

@shared_task
def check_upcoming_matches():
    """
        Check if any NOT STARTED match start_date is within 20 minutes but hasn't started yet and 
        sets its state to pending
    """
    start_time = now() + timedelta(minutes=20)
    matches = Match.objects.filter(
        start_date__gte=now(), 
        start_date__lte=start_time,
        match_state=Match.NOT_STARTED_MATCH
    )
    
    for c_match in matches:
        c_match.match_state = Match.PENDING_MATCH
        c_match.save()


@shared_task
def finalize_matches():
    """
        Check if any match pending match is already finished, change its state to
        FINALIZED and update the match result points
    """
    TIMEZONE = 'America/Argentina/Ushuaia'
    pending_matches = Match.objects.filter(
        state=True, 
        match_state=Match.PENDING_MATCH
    ).select_related('round__league', 'team_1', 'team_2')
    url = f'https://v3.football.api-sports.io/fixtures?&timezone={TIMEZONE}'
    headers = {
        'x-apisports-key': config('API_FOOTBALL_KEY')
    }
    for match in pending_matches:
        if match.api_match_id:
            url = url + f'&id={match.api_match_id}'
            response = requests.get(url, headers=headers)
            response_obj = json.loads(response.text)
            match_response = response_obj.get('response')[0]
            goals_home = match_response.get('goals').get('home')
            goals_away = match_response.get('goals').get('away')
            fixture_status = match_response.get('fixture').get('status')
            long = fixture_status.get('long')

            if long == 'Match Finished':
                try:
                    # Send push notifications to inform about the finalized match
                    send_push_nots_match(
                        team_1_name=match.team_1.name, 
                        team_2_name=match.team_2.name, 
                        goals_home=goals_home, 
                        goals_away=goals_away, 
                        league=match.round.league
                    )
                except Exception as err:
                    capture_message(f'Error sending push nots: {str(err)}', level="error")
                original_match_result, was_created = MatchResult.objects.get_or_create(
                    original_result=True,
                    match=match,
                    defaults={
                        'goals_team_1': goals_home,
                        'goals_team_2': goals_away
                    }
                )
                user_match_results = MatchResult.objects.filter(
                    state=True,
                    match=match,
                    original_result=False
                )

                with transaction.atomic(): 
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


@shared_task
def update_matches_start_date():
    """
        Update any changes in the NOT_STARTED matches start dates and update 
        Round start_date based on this
    """
    TIMEZONE = 'America/Argentina/Ushuaia'

    # Not started matches with None start_date or that would start in up to 1 month
    up_to_one_month = now() + timedelta(days=30)
    matches = Match.objects.filter(
        Q(start_date__lte=up_to_one_month, start_date__gte=now()) |
        Q(start_date__isnull=True),
        state=True,
        match_state=Match.NOT_STARTED_MATCH,
    )

    url = f'https://v3.football.api-sports.io/fixtures?timezone={TIMEZONE}'
    for match in matches:
        url += f'&id={match.api_match_id}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)

        match_response = response_obj.get('response')[0]
        fixture_data = match_response.get('fixture')
        start_date = parser.parse(fixture_data.get('date'))
        match_start_date = localtime(match.start_date)
        
        if start_date != match_start_date:
            match.start_date = start_date
            match.save()

    rounds = Round.objects.filter(matches__in=matches).distinct()
    for round in rounds:
        round.update_start_date()
