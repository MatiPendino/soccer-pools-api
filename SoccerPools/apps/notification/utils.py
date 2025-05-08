import json
import os
from decouple import config
from google.oauth2 import service_account
from pyfcm import FCMNotification
from sentry_sdk import capture_message
from .models import FCMToken

def get_fcm_object():
    credentials_path = config('GOOGLE_APPLICATION_CREDENTIALS')

    # Check if file exists
    if not os.path.exists(credentials_path):
        print('I should never be here')

    # Read the JSON file and convert to a dictionary
    with open(credentials_path) as f:
        gcp_json_credentials_dict = json.load(f)

    # Load credentials from JSON dictionary
    credentials = service_account.Credentials.from_service_account_info(
        gcp_json_credentials_dict, scopes=['https://www.googleapis.com/auth/firebase.messaging']
    )

    fcm = FCMNotification(
        service_account_file=None, 
        credentials=credentials, 
        project_id=config('FIREBASE_PROJECT_ID')
    )

    return fcm


def send_push_nots_match(team_1_name, team_2_name, goals_home, goals_away, league):
    notification_title = f'FINALIZADO: {team_1_name} {goals_home} - {goals_away} {team_2_name}'
    notification_body = 'Mira tus resultados actualizados!'

    fcm_tokens = FCMToken.objects.filter(
        state=True, 
        leagues=league
    )
    fcm = get_fcm_object()
    for fcm_token in fcm_tokens:
        try:
            result = fcm.notify(
                fcm_token=fcm_token.token_id, 
                notification_title=notification_title, 
                notification_body=notification_body
            )
        except:
            pass


def send_push_winner(user, name, coins_prize):
    notification_title = f'GANASTE {coins_prize} MONEDAS!'
    notification_body = f'Felicidades! Has ganado monedas en {name} gracias a tus habilidades;)'

    fcm_token = FCMToken.objects.filter(
        state=True, 
        user=user
    ).first()
    if not fcm_token:
        return
    
    fcm = get_fcm_object()
    try:
        result = fcm.notify(
            fcm_token=fcm_token.token_id, 
            notification_title=notification_title, 
            notification_body=notification_body
        )
    except:
        pass


def send_push_finalized_league(league):
    notification_title = f'{league.name} HA FINALIZADO!'
    notification_body = 'Mira tus resultados actualizados!'

    fcm_tokens = FCMToken.objects.filter(
        state=True, 
        leagues=league
    )
    fcm = get_fcm_object()
    for fcm_token in fcm_tokens:
        try:
            result = fcm.notify(
                fcm_token=fcm_token.token_id, 
                notification_title=notification_title, 
                notification_body=notification_body
            )
        except:
            pass


def send_push_new_round_available(round_name, league):
    """Send a push notification to all league users when a new round is available"""
    notification_title = f'{round_name} disponible en la {league.name}!'
    notification_body = 'Agrega tus resultados ahora!'

    fcm_tokens = FCMToken.objects.filter(
        state=True, 
        leagues=league
    )
    fcm = get_fcm_object()
    for fcm_token in fcm_tokens:
        try:
            result = fcm.notify(
                fcm_token=fcm_token.token_id, 
                notification_title=notification_title, 
                notification_body=notification_body
            )
        except:
            pass