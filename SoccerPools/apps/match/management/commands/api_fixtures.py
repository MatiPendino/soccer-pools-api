import requests
import json
from decouple import config
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int)
        parser.add_argument('season', type=int)
        parser.add_argument('round', type=str, nargs='?')
    
    def handle(self, *args, **options):
        TIMEZONE = 'America/Argentina/Ushuaia'
        league_id = options.get('league_id')
        season = options.get('season')
        round = options.get('round')

        url = f'https://v3.football.api-sports.io/fixtures?league={league_id}&season={season}&timezone={TIMEZONE}'
        print(round)
        if round:
            url = f'{url}&round={round}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')

        matches = response_obj.get('response')
        for match in matches:
            fixture_data = match.get('fixture')
            fixture_id = fixture_data.get('id')
            start_date = fixture_data.get('date')
            fixture_status = fixture_data.get('status')
            long = fixture_status.get('long')
            short = fixture_status.get('short')
            round = match.get('league').get('round')
            teams = match.get('teams')
            home_id = teams.get('home').get('id')
            away_id = teams.get('away').get('id')
            home_name = teams.get('home').get('name')
            away_name = teams.get('away').get('name')
            goals_home = match.get('goals').get('home')
            goals_away = match.get('goals').get('away')
            print(f'{home_name} {goals_home} - {goals_away} {away_name}')
            print(f'Fixture Id: {fixture_id} Start Date: {start_date} Round: {round}')
            print(f'Fixture status: {long} = {short}')
            print('')


        print(response.status_code)