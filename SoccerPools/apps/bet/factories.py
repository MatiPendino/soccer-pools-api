import factory
from apps.app_user.factories import AppUserFactory
from apps.league.factories import RoundFactory
from .models import BetRound
from .utils import generate_unique_code

class BetRoundFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BetRound

    user = factory.SubFactory(AppUserFactory)
    operation_code = generate_unique_code()
    round = factory.SubFactory(RoundFactory)
    