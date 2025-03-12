from celery import shared_task
from django.utils.timezone import now, timedelta
from django.db.models import Q, Count
from apps.match.models import Match
from .models import Round

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
    """Finalize all PENDING rounds where all its matches are FINALIZED"""

    pending_rounds = Round.objects.annotate(
        non_finalized_matches=Count(
            'matches',
            filter=Q(
                matches__match_state__in=[Match.NOT_STARTED_MATCH, Match.PENDING_MATCH], 
                matches__state=True
            )
        )
    ).filter(state=True, round_state=Round.PENDING_ROUND, non_finalized_matches=0)

    pending_rounds.update(round_state=Round.FINALIZED_ROUND)