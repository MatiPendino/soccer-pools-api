from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Match

@shared_task
def check_upcoming_matches():
    """
        Check if any match start_date is within 20 minutes but hasn't started yet and 
        sets its state to pending
    """
    start_time = now() + timedelta(minutes=20)
    matches = Match.objects.filter(start_date__gte=now(), start_date__lte=start_time)
    
    for c_match in matches:
        c_match.match_state = Match.PENDING_MATCH
        c_match.save()
        print(f"Upcoming match: {c_match} starts at {c_match.start_date}")