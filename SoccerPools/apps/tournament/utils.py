from decouple import config
import requests
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from apps.notification.utils import send_push_new_tournament_user_request, send_push_tournament_user_accepted
from .models import Tournament, TournamentUser

def generate_default_logo():
    RELATIVE_DEFAULT_LOGO_URL = f'{Tournament.LOGO_FOLDER_NAME}/{Tournament.LOGO_DEFAULT_FILE_NAME}'
    ABSOLUTE_DEFAULT_LOGO_URL = f'{config("AWS_S3_BUCKET_URL")}/{RELATIVE_DEFAULT_LOGO_URL}'

    response = requests.get(ABSOLUTE_DEFAULT_LOGO_URL)
    if response.status_code == 200:
        image_data = response.content
        image_file = BytesIO(image_data)
        file = InMemoryUploadedFile(image_file, None, RELATIVE_DEFAULT_LOGO_URL, 'image/png', len(image_data), None)
        return file
    else:
        raise Exception
    

def send_tournament_user_notification(user, tournament_user, tournament_state):
    """
        Send a push notification when a tournament user state is updated

        If the request is made by the tournament admin, it means that the admin is 
        accepting or rejecting a user. Send a notification to the user

        If the request is made by a user, it means that the user is requesting to join
        the tournament. Send a notification to the tournament admin
    """
    if tournament_user.tournament.admin_tournament == user:
        if tournament_state == TournamentUser.ACCEPTED:
            send_push_tournament_user_accepted(
                user=tournament_user.user,
                tournament_name=tournament_user.tournament.name,
            )
    else:
        send_push_new_tournament_user_request(
            tournament_user_admin=tournament_user.tournament.admin_tournament,
            tournament_name=tournament_user.tournament.name,
            requesting_user_username=tournament_user.user.username
        )
