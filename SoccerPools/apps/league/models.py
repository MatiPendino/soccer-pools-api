from django.db import models
from django.db.models import F
from utils import generate_unique_field_value
from apps.base.models import BaseModel
from .utils import get_coins_prize_player_based


class League(BaseModel):
    NOT_STARTED_LEAGUE = 0
    PENDING_LEAGUE = 1
    FINALIZED_LEAGUE = 2
    STATE_CODES = (
        (NOT_STARTED_LEAGUE, 'Not started'),
        (PENDING_LEAGUE, 'Pending'),
        (FINALIZED_LEAGUE, 'Finalized'),
    )

    AMERICAS = 0
    EUROPE = 1
    AFRICA = 2
    ASIA = 3
    OCEANIA = 4
    TOURNAMENTS = 5
    LEAGUE_CONTINENTS = (
        (AMERICAS, 'Americas'),
        (EUROPE, 'Europe'),
        (AFRICA, 'Africa'),
        (ASIA, 'Asia'),
        (OCEANIA, 'Oceania'),
        (TOURNAMENTS, 'Tournaments'),
    )

    # Multipliers for Coin Prizes
    COINS_FIRST_PRIZE_MULT = 250
    COINS_SECOND_PRIZE_MULT = 100
    COINS_THIRD_PRIZE_MULT = 50

    # Minimum Coin Prizes
    MIN_COINS_FIRST_PRIZE = 10000
    MIN_COINS_SECOND_PRIZE = 4000
    MIN_COINS_THIRD_PRIZE = 2000

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField('Logo of the league', upload_to='league', blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    continent = models.PositiveSmallIntegerField(default=0, choices=LEAGUE_CONTINENTS)
    api_league_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    coins_cost = models.PositiveIntegerField(default=1000)
    is_cup = models.BooleanField(help_text='If True, this league has a Cup format', default=False)
    league_state = models.PositiveSmallIntegerField('State of the league', default=0, choices=STATE_CODES)
    
    @property
    def coins_prizes(self):
        """Calculate the coin prizes for the league"""

        # Calculate the prizes based on the number of bet leagues and the multipliers
        bet_leagues_count = self.bet_leagues.count()
        prize_first_player_based = bet_leagues_count * League.COINS_FIRST_PRIZE_MULT
        prize_second_player_based = bet_leagues_count * League.COINS_SECOND_PRIZE_MULT
        prize_third_player_based = bet_leagues_count * League.COINS_THIRD_PRIZE_MULT

        # Return the prizes ensuring they are at least the minimum values
        return {
            'coins_prize_first': max(prize_first_player_based, League.MIN_COINS_FIRST_PRIZE),
            'coins_prize_second': max(prize_second_player_based, League.MIN_COINS_SECOND_PRIZE),
            'coins_prize_third': max(prize_third_player_based, League.MIN_COINS_THIRD_PRIZE),
        }

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_field_value(League, 'slug', self.name)
        super().save(*args, **kwargs)
    

class Round(BaseModel):
    NOT_STARTED_ROUND = 0
    PENDING_ROUND = 1
    FINALIZED_ROUND = 2
    STATE_CODES = (
        (NOT_STARTED_ROUND, 'Not started'),
        (PENDING_ROUND, 'Pending'),
        (FINALIZED_ROUND, 'Finalized'),
    )

    # Multipliers for Coin Prizes
    COINS_FIRST_PRIZE_MULT = 50
    COINS_SECOND_PRIZE_MULT = 20
    COINS_THIRD_PRIZE_MULT = 10

    # Minimum Coin Prizes
    MIN_COINS_FIRST_PRIZE = 1000
    MIN_COINS_SECOND_PRIZE = 400
    MIN_COINS_THIRD_PRIZE = 200

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    number_round = models.PositiveSmallIntegerField('Number of round', blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    round_state = models.PositiveSmallIntegerField('State of the round', default=0, choices=STATE_CODES)
    pool = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    price_bet = models.DecimalField('Price of the bet', max_digits=10, decimal_places=2,  help_text='This is the amount which will be added to the pool', default=0)
    fee_bet = models.DecimalField('Fee of the bet', max_digits=7, decimal_places=2, help_text='This is the amount for the platform', default=0)
    league = models.ForeignKey(League, related_name='rounds', on_delete=models.CASCADE)
    is_general_round = models.BooleanField(default=False)
    api_round_name = models.CharField(max_length=60, blank=True, null=True)

    @property
    def coins_prizes(self):
        """Calculate the coin prizes for the round"""

        # Calculate the prizes based on the number of bet rounds and the multipliers
        bet_rounds_count = self.bet_rounds.count()
        prize_first_player_based = get_coins_prize_player_based(
            bet_rounds_count, self.is_general_round, Round.COINS_FIRST_PRIZE_MULT, League.COINS_FIRST_PRIZE_MULT
        )
        prize_second_player_based = get_coins_prize_player_based(
            bet_rounds_count, self.is_general_round, Round.COINS_SECOND_PRIZE_MULT, League.COINS_SECOND_PRIZE_MULT
        )
        prize_third_player_based = get_coins_prize_player_based(
            bet_rounds_count, self.is_general_round, Round.COINS_THIRD_PRIZE_MULT, League.COINS_THIRD_PRIZE_MULT
        )

        # Ensure the prizes are at least the minimum values, considering if it is a general round or not
        if self.is_general_round:
            coins_prize_first = max(prize_first_player_based, League.MIN_COINS_FIRST_PRIZE)
            coins_prize_second = max(prize_second_player_based, League.MIN_COINS_SECOND_PRIZE)
            coins_prize_third = max(prize_third_player_based, League.MIN_COINS_THIRD_PRIZE)
        else:
            coins_prize_first = max(prize_first_player_based, Round.MIN_COINS_FIRST_PRIZE)
            coins_prize_second = max(prize_second_player_based, Round.MIN_COINS_SECOND_PRIZE)
            coins_prize_third = max(prize_third_player_based, Round.MIN_COINS_THIRD_PRIZE)

        return {
            'coins_prize_first': coins_prize_first,
            'coins_prize_second': coins_prize_second,
            'coins_prize_third': coins_prize_third,
        }

    def __str__(self):
        return f'{self.name} - {self.league}'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_field_value(Round, 'slug', self.name)
        super().save(*args, **kwargs)

    def update_start_date(self):
        """Update the Round start_date based on its earliest match start_date"""
        from apps.match.models import Match 

        earliest_match_dt = self.matches.filter(
            match_state__in=[Match.NOT_STARTED_MATCH, Match.PENDING_MATCH, Match.FINALIZED_MATCH],
            start_date__isnull=False,
            state=True,
        ).order_by('start_date').values_list('start_date', flat=True).first()

        if earliest_match_dt is not None and self.start_date != earliest_match_dt:
            self.start_date = earliest_match_dt
            self.save(update_fields=['start_date'])

    def get_league_name(self):
        """Get the league name of the round"""
        return self.league.name if self.league else None

    def update_round_winners_prizes(self, competition_name):
        """
            Update the winners of the round and distribute coins to the winners.
        """
        from apps.bet.models import BetRound
        from apps.bet.services import update_top_three_bet_league_winners
        from apps.notification.utils import send_push_winner

        # Get the first three bet rounds of the round
        first_bet_round, second_bet_round, third_bet_round = BetRound.objects.with_matches_points(
            round_slug=self.slug
        )[:3]

        # Get the first three users of the bet rounds
        first_user = first_bet_round.get_user()
        second_user = second_bet_round.get_user()
        third_user = third_bet_round.get_user()

        # Update the winners of the bet rounds
        first_bet_round.winner_first = True
        second_bet_round.winner_second = True
        third_bet_round.winner_third = True
        first_bet_round.save()
        second_bet_round.save()
        third_bet_round.save()

        # If the round is a league, update the winners of the bet leagues too
        if self.is_general_round:
            update_top_three_bet_league_winners(
                league=self.league, first_user=first_user, second_user=second_user, third_user=third_user
            )

        # Distribute coins to the winners
        n_bet_rounds = self.bet_rounds.count()
        if self.is_general_round:
            first_prize = n_bet_rounds * League.COINS_FIRST_PRIZE_MULT
            second_prize = n_bet_rounds * League.COINS_SECOND_PRIZE_MULT
            third_prize = n_bet_rounds * League.COINS_THIRD_PRIZE_MULT
        else:
            first_prize = n_bet_rounds * Round.COINS_FIRST_PRIZE_MULT
            second_prize = n_bet_rounds * Round.COINS_SECOND_PRIZE_MULT
            third_prize = n_bet_rounds * Round.COINS_THIRD_PRIZE_MULT

        first_user.coins = F('coins') + first_prize
        second_user.coins = F('coins') + second_prize
        third_user.coins = F('coins') + third_prize
        first_user.save()
        second_user.save()
        third_user.save()

        # Send push notifications to the winners
        send_push_winner(first_user, competition_name, first_prize)
        send_push_winner(second_user, competition_name, second_prize)
        send_push_winner(third_user, competition_name, third_prize)


class Team(BaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, null=True, blank=True)
    acronym = models.CharField(max_length=5, null=True, blank=True, help_text='Shorter way to display team name')
    badge = models.ImageField('Badge of the team', upload_to='league', null=True, blank=True)
    badge_url = models.URLField(null=True, blank=True)
    leagues = models.ManyToManyField(League, related_name='teams')
    api_team_id = models.PositiveIntegerField(unique=True, blank=True, null=True)

    def __str__(self):
        return f'{self.name} - {self.api_team_id}'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_field_value(Team, 'slug', self.name)
        super().save(*args, **kwargs)
    

