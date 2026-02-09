import random
from faker import Faker
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.core.management.base import BaseCommand 
from django.db import transaction
from django.core.files.base import ContentFile
from django.db.models import Q
from apps.match.models import Match, MatchResult
from apps.app_user.models import AppUser
from apps.league.models import League, Round
from apps.bet.models import BetRound, BetLeague

GOOGLEY_BG_HEX = [
    "F44336", "E91E63", "9C27B0", "673AB7", "3F51B5", "2196F3",
    "03A9F4", "00BCD4", "009688", "4CAF50", "8BC34A", "CDDC39",
    "FFEB3B", "FFC107", "FF9800", "FF5722", "795548", "607D8B", "9E9E9E",
]

def generate_google_avatar(letter, bg_color_hex, size=200):
    """Generate a Google-style circular avatar with a single letter"""
    # Convert hex to RGB
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4))

    # Create circular image with colored background
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw filled circle
    draw.ellipse([0, 0, size, size], fill=bg_color)

    # Calculate font size 
    font_size = int(size * 0.45)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Get text bounding box for centering
    letter_upper = letter.upper()
    bbox = draw.textbbox((0, 0), letter_upper, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position to center text
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    # Draw white text
    draw.text((x, y), letter_upper, fill='white', font=font)

    # Save to BytesIO
    output = BytesIO()
    image.save(output, format='PNG')
    output.seek(0)

    return output

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('league_name', type=str)
        parser.add_argument('num_players', type=int, default=2)
    
    def handle(self, *args, **options):
        num_players = options.get('num_players', 2)
        league_name = options.get('league_name')
        league = get_object_or_404(League, name=league_name)

        fake = Faker('es_AR')
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

        for player_data in players_data:
            # User and Profile Image creation
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
                # Generate Google-style avatar with first letter
                bg_color = random.choice(GOOGLEY_BG_HEX)
                avatar_image = generate_google_avatar(name[0], bg_color)

                # Save to the ImageField
                filename = f"avatars/{username}.png"
                user.profile_image.save(filename, ContentFile(avatar_image.read()), save=True)

                self.stdout.write(self.style.SUCCESS(
                    f"Generated avatar for {username} with letter '{name[0].upper()}' on #{bg_color}"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Failed to generate avatar for {username}: {e}"
                ))


            # BetLeague, BetRound and MatchResult creation
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
 
        
