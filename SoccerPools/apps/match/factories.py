import factory
from apps.league.factories import TeamFactory, RoundFactory
from apps.bet.factories import BetRoundFactory
from apps.match.models import Match, MatchResult

class MatchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Match

    team_1 = factory.SubFactory(TeamFactory)
    team_2 = factory.SubFactory(TeamFactory)
    round = factory.SubFactory(RoundFactory)
    match_state = Match.NOT_STARTED_MATCH
    start_date = None
    api_match_id = None


class MatchResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MatchResult

    goals_team_1 = None
    goals_team_2 = None
    bet_round = factory.SubFactory(BetRoundFactory)
    match = factory.SubFactory(MatchFactory)
    points = 0