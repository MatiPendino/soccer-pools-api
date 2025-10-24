import requests
import random
from mimetypes import guess_extension
from faker import Faker
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.management.base import BaseCommand 
from django.db import transaction
from django.db.models import Q
from apps.match.models import Match, MatchResult
from apps.app_user.models import AppUser
from apps.league.models import League, Round
from apps.bet.models import BetRound, BetLeague

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_name', type=str)
        parser.add_argument('num_players', type=int, default=2)
    
    def handle(self, *args, **options):
        num_players = options.get('num_players', 2)
        league_name = options.get('league_name')
        league = get_object_or_404(League, name=league_name)

        fake = Faker('es_ES')
        players_data = []
        for _ in range(num_players):
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}{last_name.lower()}@gmail.com"

            players_data.append({
                'email': email,
                'name': first_name,
                'last_name': last_name,
            })

        base_url = 'https://avatar.iran.liara.run/username?color=ffffff&username='
        for player_data in players_data:
            ####### User and Profile Image creation ########
            email = player_data['email']
            name = player_data['name']
            last_name = player_data['last_name']
            username = slugify(f'{name}-{last_name}')
            password = 'defaultpassword123'

            user, created = AppUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'name': name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password(password)
                user.save()

            try:
                url = f"{base_url}{name[0]}"
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()

                # Make sure we actually got an image
                ctype = resp.headers.get('Content-Type', '')
                if not ctype.startswith('image/'):
                    self.stdout.write(self.style.WARNING(
                        f"Skipped avatar for {username}: unexpected content-type '{ctype}'"
                    ))
                    continue

                # Pick a sensible file extension
                ext = guess_extension(ctype.split(';')[0]) or '.png'
                filename = f"avatars/{username}{ext}"

                # Save to the ImageField
                user.profile_image.save(filename, ContentFile(resp.content), save=True)
                self.stdout.write(self.style.SUCCESS(f"Set avatar for {username}"))

            except requests.RequestException as e:
                print(f"Failed to fetch avatar for {username}: {e}")


            ####### BetLeague, BetRound and MatchResult creation ########
            # Filter all the NON finalized rounds
            rounds = Round.objects.filter(
                Q(round_state=Round.NOT_STARTED_ROUND) | 
                Q(round_state=Round.PENDING_ROUND),
                state=True,
                league=league,
            )

            # BetLeague, BetRound and MatchResult creation
            with transaction.atomic():
                # Create bet_league
                new_bet_league = BetLeague.objects.create(
                    user=user, 
                    league=league, 
                    is_last_visited_league=True
                )

                # Create bet rounds for the league rounds that are NOT finalized
                bet_rounds = [
                    BetRound(round=league_round, bet_league=new_bet_league) 
                    for league_round in rounds
                ]
                BetRound.objects.bulk_create(bet_rounds)

                # Create match results for all the matches in all the bet rounds
                for bet_round in bet_rounds:
                    matches = Match.objects.filter(round=bet_round.round, state=True)
                    match_results = [
                        MatchResult(
                            match=soccer_match, 
                            bet_round=bet_round,
                            goals_team_1=random.randint(0, 5),
                            goals_team_2=random.randint(0, 5)
                        ) 
                        for soccer_match in matches
                    ]
                    MatchResult.objects.bulk_create(match_results)
 
        
