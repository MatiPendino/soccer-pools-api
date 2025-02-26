import requests
import json
from decouple import config
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from apps.league.models import Round, Team, League
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

        league = get_object_or_404(League, state=True, api_league_id=league_id)

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

        matches = response_obj.get('response')
        n_created_matches = 0
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

            if short in ['TBD', 'NS']:
                round = get_object_or_404(Round, state=True, league=league, api_round_name=round)
                team_1 = get_object_or_404(Team, state=True, league=league, api_team_id=home_id)
                team_2 = get_object_or_404(Team, state=True, league=league, api_team_id=away_id)

                Match.objects.get_or_create(
                    round=round,
                    team_1=team_1,
                    team_2=team_2,
                    api_match_id=fixture_id,
                    defaults={
                        'start_date': start_date
                    }
                )
                n_created_matches += 1
        
        print(f'{n_created_matches} Matches created, league {league}')