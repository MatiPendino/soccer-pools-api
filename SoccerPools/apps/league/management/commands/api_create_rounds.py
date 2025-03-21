import requests
import json
from decouple import config
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.league.models import Round, League

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_id', type=int)
        parser.add_argument('season', type=int)
    
    def handle(self, *args, **options):
        league_id = options.get('league_id')
        season = options.get('season')

        league = get_object_or_404(League, state=True, api_league_id=league_id)

        url = f'https://v3.football.api-sports.io/fixtures/rounds?league={league_id}&season={season}'
        headers = {
            'x-apisports-key': config('API_FOOTBALL_KEY')
        }
        response = requests.get(url, headers=headers)
        response_obj = json.loads(response.text)
        print(f'Results: {response_obj.get("results")}')
        print(response.text)
        print(response.status_code)
        rounds = response_obj.get('response')
        n_created_rounds = 0
        for i, round in enumerate(rounds, start=1):
            Round.objects.create(
                league=league,
                name=round,
                api_round_name=round,
                number_round=i
            )
            n_created_rounds += 1

        Round.objects.create( # General Round creation
            league=league,
            number_round=0,
            name='General',
            is_general_round=True
        )
        n_created_rounds += 1

        print(f'{n_created_rounds} new Rounds created for {league}')