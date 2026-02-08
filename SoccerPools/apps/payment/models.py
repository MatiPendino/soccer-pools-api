import uuid
from django.db import models
from apps.base.models import BaseModel
from apps.app_user.models import AppUser
from apps.league.models import League, Round

class PaidLeagueConfig(BaseModel):
    league = models.OneToOneField(League, on_delete=models.CASCADE, related_name='paid_config')
    is_paid_mode_enabled = models.BooleanField(default=False)
    round_price_ars = models.DecimalField(max_digits=10, decimal_places=2)
    league_price_ars = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)
    start_round_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Paid League Config'
        verbose_name_plural = 'Paid League Configs'

    def __str__(self):
        status = 'enabled' if self.is_paid_mode_enabled else 'disabled'
        return f'{self.league.name} - Paid mode {status}'


class Payment(BaseModel):
    PAYMENT_TYPE_ROUND = 'round'
    PAYMENT_TYPE_LEAGUE = 'league'
    PAYMENT_TYPE_CHOICES = (
        (PAYMENT_TYPE_ROUND, 'Round'),
        (PAYMENT_TYPE_LEAGUE, 'League'),
    )

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDED = 'refunded'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REFUNDED, 'Refunded'),
    )

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    mp_preference_id = models.CharField(
        'MercadoPago Preference ID', max_length=255, blank=True, null=True
    )
    mp_payment_id = models.CharField(
        'MercadoPago Payment ID', max_length=255, blank=True, null=True
    )
    gross_amount_ars = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee_ars = models.DecimalField(max_digits=10, decimal_places=2)
    prize_pool_ars = models.DecimalField(max_digits=10, decimal_places=2)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='payments')
    round = models.ForeignKey(
        Round, on_delete=models.CASCADE, related_name='payments', null=True, blank=True
    )
    external_reference = models.CharField(
        max_length=100, unique=True, help_text='Unique reference for MercadoPago tracking'
    )

    def __str__(self):
        return f'{self.user.username} - {self.payment_type} - {self.status}'

    def save(self, *args, **kwargs):
        if not self.external_reference:
            self.external_reference = f'sp_{uuid.uuid4().hex[:16]}'
        super().save(*args, **kwargs)


class PaidBetRound(BaseModel):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='paid_bet_rounds')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='paid_bet_rounds')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='paid_bet_rounds')
    winner_first = models.BooleanField(default=False)
    winner_second = models.BooleanField(default=False)
    winner_third = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Paid Bet Round'
        verbose_name_plural = 'Paid Bet Rounds'
        unique_together = ('user', 'round')

    def __str__(self):
        return f'{self.user.username} - {self.round.name}'

    @property
    def points(self):
        """Calculate total points from match results"""
        return self.match_results.aggregate(
            total_points=models.Sum('points')
        )['total_points'] or 0

    @property
    def exact_results(self):
        """Count exact result predictions"""
        return self.match_results.filter(
            is_exact=True,
            state=True
        ).count()


class PaidPrizePool(BaseModel):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='paid_prize_pools')
    round = models.ForeignKey(
        Round, on_delete=models.CASCADE, related_name='paid_prize_pools', null=True, blank=True
    )
    is_league_pool = models.BooleanField(default=False)
    total_pool_ars = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    distributed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Paid Prize Pool'
        verbose_name_plural = 'Paid Prize Pools'

    def __str__(self):
        return f'{self.league.name} - ${self.total_pool_ars}'


class PaidWinner(BaseModel):
    CONTACT_STATUS_PENDING = 0
    CONTACT_STATUS_CONTACTED = 1
    CONTACT_STATUS_PAID = 2
    CONTACT_STATUS_CHOICES = (
        (CONTACT_STATUS_PENDING, 'Pending'),
        (CONTACT_STATUS_CONTACTED, 'Contacted'),
        (CONTACT_STATUS_PAID, 'Paid'),
    )

    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='paid_wins')
    prize_pool = models.ForeignKey(
        PaidPrizePool, on_delete=models.CASCADE, related_name='winners'
    )
    position = models.PositiveSmallIntegerField()
    prize_amount_ars = models.DecimalField(max_digits=10, decimal_places=2)
    contact_status = models.PositiveSmallIntegerField(
        choices=CONTACT_STATUS_CHOICES, default=CONTACT_STATUS_PENDING
    )
    admin_notes = models.TextField(
        blank=True, null=True, help_text='Notes from admin about payout status'
    )

    class Meta:
        verbose_name = 'Paid Winner'
        verbose_name_plural = 'Paid Winners'

    def __str__(self):
        position_name = {1: '1st', 2: '2nd', 3: '3rd'}.get(self.position, f'{self.position}th')
        return f'{self.user.username} - {position_name} place - ${self.prize_amount_ars}'
