from django.core.management.base import BaseCommand
from apps.league.models import Round

class Command(BaseCommand):
    """List the last rounds id and name"""
    def add_arguments(self, parser):
        parser.add_argument('length', type=int)


    def handle(self, *args, **options):
        rounds_queryset_length = options['length']
        rounds = Round.objects.filter(state=True).order_by('-id')[:rounds_queryset_length].values('id', 'name')

        self.stdout.write(
            self.style.SUCCESS(rounds)
        )