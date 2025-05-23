import factory
from .models import League, Round, Team

class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = League
    
    name = factory.Faker('word')
    slug = factory.Faker('word')
    continent = League.AMERICAS
    league_state = League.NOT_STARTED_LEAGUE
    is_cup = False
    coins_cost = 1000

class RoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Round

    name = factory.Faker('word')
    number_round = factory.Faker('random_int', min=0, max=100)
    round_state = Round.NOT_STARTED_ROUND
    league = factory.SubFactory(LeagueFactory)
    is_general_round = False
    start_date = None


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Faker('word')
    @factory.post_generation
    def leagues(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            self.leagues.set(extracted)
