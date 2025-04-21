import factory
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory, RoundFactory
from .models import BetLeague, BetRound


class BetLeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BetLeague

    user = factory.SubFactory(AppUserFactory)
    league = factory.SubFactory(LeagueFactory)
    is_last_visited_league = False


class BetRoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BetRound

    round = factory.SubFactory(RoundFactory)
    bet_league = factory.SubFactory(BetLeagueFactory)