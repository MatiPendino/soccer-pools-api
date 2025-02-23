import requests
import json
from decouple import config
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        url = 'https://v3.football.api-sports.io/timezone'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')
        timezones = response_obj.get('response')
        for timezone in timezones:
            print(timezone)

        print(response.status_code)
