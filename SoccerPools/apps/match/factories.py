import factory
from apps.league.factories import TeamFactory, RoundFactory
from apps.bet.factories import BetFactory
from apps.match.models import Match, MatchResult

class MatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Match

    team_1 = factory.SubFactory(TeamFactory)
    team_2 = factory.SubFactory(TeamFactory)
    round = factory.SubFactory(RoundFactory)


class MatchResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MatchResult

    bet = factory.SubFactory(BetFactory)
    match = factory.SubFactory(MatchFactory)
    points = 0