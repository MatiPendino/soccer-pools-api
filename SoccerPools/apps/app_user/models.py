from django.db import models, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.apps import apps
from django.utils import timezone
from django.conf import settings
from apps.base.models import BaseModel
from .validations import validate_no_spaces
from .utils import generate_referral_code

class AppUserManager(BaseUserManager):
    def _create_user(
        self, username, email, name, last_name, password, is_staff, is_superuser, **extra_fields):
        user = self.model(
            username=username,
            email=email,
            name=name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **extra_fields
        )
        user.set_password(password)
        user.save()
        return user
        
    def create_user(self, username, email, name, last_name, password=None, **extra_fields):
        if not username:
            raise ValidationError('A username is required.')
        if not email:
            raise ValidationError('An email is required.')
        if not password:
            raise ValidationError('A password is required.')
        return self._create_user(username, email, name, last_name, password, False, False, **extra_fields)

    def create_superuser(self, username, email, name, last_name, password=None, **extra_fields):
        if not username:
            raise ValidationError('A username is required.')
        if not email:
            raise ValidationError('An email is required.')
        if not password:
            raise ValidationError('A password is required.')
        return self._create_user(username, email, name, last_name, password, True, True, **extra_fields)

class AppUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True, validators=[validate_no_spaces])
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='profile', default='default-profile-image.png')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    coins = models.PositiveIntegerField(default=5000)
    created_at = models.DateTimeField(default=timezone.now, null=True)
    instagram_username = models.CharField(max_length=255, blank=True, null=True)
    twitter_username = models.CharField(max_length=255, blank=True, null=True)
    referral_code = models.CharField(
        max_length=12, unique=True, blank=True, null=True, default=generate_referral_code
    )
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, blank=True, null=True, related_name='referrals'
    )
    
    objects = AppUserManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('email', 'name', 'last_name')

    def __str__(self):
        return self.username
    
    def remove_user(self):
        """
            Removes logically the User and its BetLeague, BetRound and MatchResult instances
        """
        BetRound = apps.get_model('bet', 'BetRound')
        BetLeague = apps.get_model('bet', 'BetLeague')
        MatchResult = apps.get_model('match', 'MatchResult')
        with transaction.atomic():
            self.is_active = False
            self.save()

            bet_leagues = BetLeague.objects.filter(user=self, state=True)
            bet_rounds = BetRound.objects.filter(bet_league__in=bet_leagues, state=True)
            match_results = MatchResult.objects.filter(bet_round__in=bet_rounds, state=True)

            match_results.update(state=False)
            bet_rounds.update(state=False)
            bet_leagues.update(state=False)


class CoinGrant(BaseModel):
    AD_REWARD_DAILY_CAP = 10
    AD_REWARD_AMOUNT = 10 if settings.DEBUG else 1000
    APP_REVIEW_AMOUNT = 2000
    REFERRAL_SIGNUP_AMOUNT = 5000
    REFERRER_EARNINGS_MULTIPLIER = 0.1

    AD_REWARD = 0
    APP_REVIEW = 1
    DAILY = 2
    REFERRAL_SIGNUP = 3
    LEAGUE_WINNER = 4
    REFERRAL_EARNED = 5

    REWARD_TYPES = [
        (AD_REWARD, 'Ad reward'), 
        (APP_REVIEW, 'App review'),
        (DAILY, 'Daily'), 
        (REFERRAL_SIGNUP, 'Referral Signup'),
        (LEAGUE_WINNER, 'League winner'),
        (REFERRAL_EARNED, 'Referral Earned'),
    ]

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='coin_grants')
    reward_type = models.PositiveSmallIntegerField(choices=REWARD_TYPES)
    amount = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} - {self.get_reward_type_display()}'
