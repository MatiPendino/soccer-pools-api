import requests
import json
from decouple import config
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int)
        parser.add_argument('season', type=int)
        parser.add_argument('only_current', type=bool)
        parser.add_argument('include_dates', type=bool)
    
    def handle(self, *args, **options):
        league_id = options.get('league_id')
        season = options.get('season')
        only_current = options.get('only_current')
        include_dates = options.get('include_dates')

        url = f'https://v3.football.api-sports.io/fixtures/rounds?league={league_id}&season={season}&current={only_current}&dates={include_dates}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')
        print(response.text)
        print(response.status_code)