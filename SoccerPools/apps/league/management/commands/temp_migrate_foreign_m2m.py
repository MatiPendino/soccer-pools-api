from django.core.management.base import BaseCommand
from apps.league.models import Team

class Command(BaseCommand):
    def handle(self, *args, **options):
        teams = Team.objects.all().select_related('league')
        for team in teams:
            team.leagues.add(team.league)
        
        print(f'{teams.count()} teams updated')