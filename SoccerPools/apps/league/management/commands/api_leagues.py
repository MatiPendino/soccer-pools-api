import requests
import json
from decouple import config
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('country', type=str)
    
    def handle(self, *args, **options):
        country = options.get('country')
        url = f'https://v3.football.api-sports.io/leagues?country={country}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')
        leagues = response_obj.get('response')
        for league in leagues:
            league_data = league.get('league')
            league_name = league_data.get('name')
            league_id = league_data.get('id')
            league_logo_url = league_data.get('logo')
            print(f'*********{league_name} - {league_id}*********')
            print(league_logo_url)

            print('*********** SEASONS ***************')
            seasons = league.get('seasons')
            for season in seasons:
                year = season.get('year')
                start_date = season.get('start')
                end_date = season.get('end')
                current = season.get('current')
                print(f'Year: {year} - Start: {start_date} - End: {end_date} - Current {current}')
            
        print(response.status_code)
