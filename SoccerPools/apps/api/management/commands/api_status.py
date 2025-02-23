import requests
from decouple import config
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = 'https://v3.football.api-sports.io/status'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)

        print(response.text)
