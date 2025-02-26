import requests
import json
from decouple import config
from django.core.management.base import BaseCommand
from apps.league.models import League

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int)

    def handle(self, *args, **options):
        league_id = options.get('league_id')
        url = f'https://v3.football.api-sports.io/leagues?id={league_id}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)

        league_response = response_obj.get('response')[0]
        league_data = league_response.get('league')

        league, was_created = League.objects.get_or_create(
            api_league_id=league_data.get('id'),
            defaults={
                'name': league_data.get('name'),
                'logo_url': league_data.get('logo')
            }
        )

        print(f'League: {league} - Created {was_created}')