from celery import shared_task
from sentry_sdk import capture_message
from django.utils.timezone import now, timedelta
from apps.league.models import Round
from .models import FCMToken
from .utils import get_fcm_object

@shared_task
def send_push_round_starting_24hs():
    """
        Check if any round start_date is within 24hs but hasn't started yet and 
        send a push not. to users registered in the league
    """
    start_time = now() + timedelta(days=1)
    rounds = Round.objects.filter(start_date__gte=now(), start_date__lte=start_time).select_related('league')

    if rounds.exists():
        fcm = get_fcm_object()
        
        for round in rounds:
            league = round.league
            fcm_tokens = FCMToken.objects.filter(state=True, leagues=league)
            notification_title = f'Esta por comenzar {round.name}'
            notification_body = 'Realiza tus predicciones antes de que inicie la fecha!'
            for fcm_token in fcm_tokens:
                try:
                    result = fcm.notify(
                        fcm_token=fcm_token.token_id, 
                        notification_title=notification_title, 
                        notification_body=notification_body
                    )
                except Exception as err:
                    pass
