from celery import shared_task
from django.utils.timezone import now, timedelta
from .models import Round

@shared_task
def check_upcoming_rounds():
    """
        Check if any round start_date is within 20 minutes but hasn't started yet and 
        sets its state to pending
    """
    start_time = now() + timedelta(minutes=20)
    rounds = Round.objects.filter(start_date__gte=now(), start_date__lte=start_time)
    
    for round in rounds:
        round.round_state = Round.PENDING_ROUND
        round.save()
        print(f"Upcoming event: {round.name} starts at {round.start_date}")
