from django.db import models
from utils import generate_unique_field_value
from apps.base.models import BaseModel


class League(BaseModel):
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

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField('Logo of the league', upload_to='league', blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    continent = models.PositiveSmallIntegerField(default=0, choices=LEAGUE_CONTINENTS)
    api_league_id = models.PositiveIntegerField(unique=True, blank=True, null=True)
    coins_cost = models.PositiveIntegerField(default=1000)
    
    @property
    def coins_prizes(self):
        bet_leagues_count = self.bet_leagues.count()

        return {
            'coins_prize_first': bet_leagues_count * League.COINS_FIRST_PRIZE_MULT,
            'coins_prize_second': bet_leagues_count * League.COINS_SECOND_PRIZE_MULT,
            'coins_prize_third': bet_leagues_count * League.COINS_THIRD_PRIZE_MULT,
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

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)
    number_round = models.PositiveSmallIntegerField('Number of round', blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    round_state = models.PositiveSmallIntegerField('State of the round', default=0, choices=STATE_CODES)
    pool = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    price_bet = models.DecimalField('Price of the bet', max_digits=10, decimal_places=2,  help_text='This is the amount which will be added to the pool', default=0)
    fee_bet = models.DecimalField('Fee of the bet', max_digits=7, decimal_places=2, help_text='This is the amount for the platform', default=0)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    is_general_round = models.BooleanField(default=False)
    api_round_name = models.CharField(max_length=60, blank=True, null=True)

    @property
    def coins_prizes(self):
        bet_rounds_count = self.bet_rounds.count()
        coins_prize_first = bet_rounds_count * (
            Round.COINS_FIRST_PRIZE_MULT if not self.is_general_round else League.COINS_FIRST_PRIZE_MULT
        )
        coins_prize_second = bet_rounds_count * (
            Round.COINS_SECOND_PRIZE_MULT if not self.is_general_round else League.COINS_SECOND_PRIZE_MULT
        )
        coins_prize_third = bet_rounds_count * (
            Round.COINS_THIRD_PRIZE_MULT if not self.is_general_round else League.COINS_THIRD_PRIZE_MULT
        )

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
        match_earliest_start_date = self.matches.order_by('start_date').first()
        self.start_date = match_earliest_start_date.start_date
        self.save()


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
    

