import requests
import json
from decouple import config
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.league.models import Team, League

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int)
        parser.add_argument('season', type=int)
    
    def handle(self, *args, **options):
        league_id = options.get('league_id')
        season = options.get('season')

        league = get_object_or_404(League, api_league_id=league_id)

        url = f'https://v3.football.api-sports.io/teams?league={league_id}&season={season}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')

        number_created_records = 0
        teams = response_obj.get('response')
        for team in teams:
            team_data = team.get('team')
            id = team_data.get('id')
            name = team_data.get('name')
            code = team_data.get('code')
            logo_url = team_data.get('logo')
            print(f'************ {name} - {id} ***************')
            print(code)
            print(logo_url)
            print('')

            """
                team, was_created = Team.objects.get_or_create(
                    api_team_id=id,
                    defaults={
                        'name': name,
                        'acronym': code,
                        'badge_url': logo_url,
                        'league': league
                    }
                )
                number_created_records += 1 if was_created else 0
            """

        print(f'{number_created_records} created records')
        print(response.status_code)
