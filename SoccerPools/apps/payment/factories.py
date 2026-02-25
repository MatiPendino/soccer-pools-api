import factory
from decimal import Decimal
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory
from apps.match.factories import MatchFactory
from .models import (
    PaidLeagueConfig, Payment, PaidBetRound, PaidPrizePool, PaidWinner,
)

class PaidLeagueConfigFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaidLeagueConfig

    league = factory.SubFactory(LeagueFactory)
    is_paid_mode_enabled = True
    round_price_ars = Decimal('500.00')
    league_price_ars = Decimal('2000.00')
    platform_fee_percentage = Decimal('25.00')


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    user = factory.SubFactory(AppUserFactory)
    payment_type = Payment.PAYMENT_TYPE_ROUND
    status = Payment.STATUS_PENDING
    gross_amount_ars = Decimal('500.00')
    platform_fee_ars = Decimal('125.00')
    prize_pool_ars = Decimal('375.00')
    league = factory.SubFactory(LeagueFactory)
    round = factory.SubFactory(RoundFactory)


class PaidBetRoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaidBetRound

    user = factory.SubFactory(AppUserFactory)
    round = factory.SubFactory(RoundFactory)
    payment = factory.SubFactory(PaymentFactory)
    winner_first = False
    winner_second = False
    winner_third = False


class PaidPrizePoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaidPrizePool

    league = factory.SubFactory(LeagueFactory)
    round = factory.SubFactory(RoundFactory)
    is_league_pool = False
    total_pool_ars = Decimal('1000.00')
    minimum_pool_ars = Decimal('0')
    distributed = False


class PaidWinnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaidWinner

    user = factory.SubFactory(AppUserFactory)
    prize_pool = factory.SubFactory(PaidPrizePoolFactory)
    position = 1
    prize_amount_ars = Decimal('600.00')
    contact_status = PaidWinner.CONTACT_STATUS_PENDING
    admin_notes = None
