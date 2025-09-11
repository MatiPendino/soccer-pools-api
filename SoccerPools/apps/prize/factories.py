import factory
from .models import Prize

class PrizeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Prize

    title = factory.Faker('word')
    image = None
    coins_cost = 1000
    description = factory.Faker('word')
    