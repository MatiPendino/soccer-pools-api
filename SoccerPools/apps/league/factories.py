import factory
from .models import League, Round, Team

class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = League
    
    name = factory.Faker('word')


class RoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Round

    name = factory.Faker('word')
    number_round = factory.Faker('random_int', min=0, max=100)
    league = factory.SubFactory(LeagueFactory)


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Faker('word')
    league = factory.SubFactory(LeagueFactory)