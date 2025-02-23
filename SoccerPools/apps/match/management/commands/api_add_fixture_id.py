import requests
import json
from decouple import config
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.match.models import Match

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
            url = url + f'&round={round}'
            print(url)
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')

        n_updated_matches = 0
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

            match_instance = get_object_or_404(
                Match, 
                team_1__api_team_id=home_id, 
                team_2__api_team_id=away_id
            )
            match_instance.api_match_id = fixture_id
            match_instance.save()
            n_updated_matches += 1
        
        print(f'{n_updated_matches} updated records')