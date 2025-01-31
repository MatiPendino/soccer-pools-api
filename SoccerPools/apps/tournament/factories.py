import factory
from apps.app_user.factories import AppUserFactory
from apps.league.factories import LeagueFactory
from apps.tournament.models import Tournament, TournamentUser

class TournamentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tournament

    name = factory.Faker('word')
    league = factory.SubFactory(LeagueFactory)
    admin_tournament = factory.SubFactory(AppUserFactory)


class TournamentUserFactory(factory.django.DjangoModelFactory): 
    class Meta:
        model = TournamentUser

    tournament = factory.SubFactory(Tournament)
    user = factory.SubFactory(AppUserFactory)
    tournament_user_state = TournamentUser.NOT_SENT