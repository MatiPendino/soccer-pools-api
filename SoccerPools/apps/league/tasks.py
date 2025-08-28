from celery import shared_task
from django.utils.timezone import now, timedelta
from django.db import transaction
from django.db.models import Q, Count, F
from django.core.mail import mail_admins
from apps.match.models import Match
from apps.notification.utils import send_push_finalized_league, send_push_finalized_round
from .models import Round, League

@shared_task
def check_upcoming_rounds():
    """
        Check if any round start_date is within 20 minutes but hasn't started yet and 
        sets its state to pending
    """
    start_time = now() + timedelta(minutes=20)
    rounds = Round.objects.filter(state=True, start_date__gte=now(), start_date__lte=start_time)
    
    for round in rounds:
        round.round_state = Round.PENDING_ROUND
        round.save()


@shared_task
def finalize_pending_rounds():
    """
        Finalize all PENDING rounds where all its matches are not NOT_STARTED or PENDING, 
        and distribute Coin Rewards
    """

    pending_rounds = Round.objects.annotate(
        non_finalized_matches=Count(
            'matches',
            filter=Q(
                matches__match_state__in=[Match.NOT_STARTED_MATCH, Match.PENDING_MATCH], 
                matches__state=True
            )
        )
    ).filter(state=True, round_state=Round.PENDING_ROUND, non_finalized_matches=0)

    with transaction.atomic():
        for pending_round in pending_rounds:
            pending_round.update_round_winners_prizes(competition_name=pending_round.name)
            send_push_finalized_round(round=pending_round)
            
        pending_rounds.update(round_state=Round.FINALIZED_ROUND)


@shared_task
def check_finalized_leagues():
    """
        Check if any league has all its rounds finalized
        If the league format is actually a league, set the league state to FINALIZED and give coin prizes 
        In case that the league format is a cup, send email to the admins to let them know and see 
        how to proceed
    """

    leagues = League.objects.filter(
        state=True,
        league_state__in=[League.PENDING_LEAGUE, League.NOT_STARTED_LEAGUE],
    ).annotate(
        non_finalized=Count(
            'rounds',
            filter=Q(rounds__state=True) & ~Q(rounds__round_state=Round.FINALIZED_ROUND)
        )
    ).filter(non_finalized=1)
    
    for league in leagues:
        if league.is_cup:
            subject = f'[ALERT] Cup {league.name} {league.id} has all the rounds FINALIZED'
            message = (
                f"League ID: {league.id}\n"
                f"API League ID: {league.api_league_id}\n"
                "Please log in to the admin panel and see how to proceed."
            )
            mail_admins(subject, message)
        else:
            with transaction.atomic():
                general_round = league.rounds.filter(is_general_round=True).first()
                general_round.update_round_winners_prizes(competition_name=league.name)
                send_push_finalized_league(league)

                league.league_state = League.FINALIZED_LEAGUE
                league.save()