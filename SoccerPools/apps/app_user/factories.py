import factory
from .models import AppUser

class AppUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppUser

    username = factory.Faker('word')
    email = factory.Faker('email')
    name = factory.Faker('word')
    last_name = factory.Faker('word')
    coins = 3000
    referred_by = None