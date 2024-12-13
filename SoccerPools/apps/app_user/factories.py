import factory
from .models import AppUser

class AppUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppUser

    username = 'User Test'
    email = 'testing@gmail.com'
    name = 'User'
    last_name = 'Test'
    