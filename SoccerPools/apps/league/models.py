from django.db import models
from django.utils.text import slugify
from apps.base.models import BaseModel


class League(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField('Logo of the league', upload_to='league', blank=True, null=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
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

    def __str__(self):
        return f'{self.name} - {self.league}'
    
    def get_number_bets(self):
        return self.bet_set.count()
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Team(BaseModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, null=True, blank=True)
    badge = models.ImageField('Badge of the team', upload_to='league', null=True, blank=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} - {self.league}'
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    

