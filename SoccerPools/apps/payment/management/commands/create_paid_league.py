from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.league.models import League, Round
from apps.payment.models import PaidLeagueConfig, PaidPrizePool


class Command(BaseCommand):
    help = 'Create a paid league configuration with all required entities'

    def add_arguments(self, parser):
        parser.add_argument(
            'league_slug',
            type=str,
        )
        parser.add_argument(
            '--round-price',
            type=Decimal,
            default=Decimal('2500.00'),
        )
        parser.add_argument(
            '--league-price',
            type=Decimal,
            default=None,
            help='Price for full league in ARS (default: 15%% discount on total rounds)'
        )
        parser.add_argument(
            '--platform-fee',
            type=Decimal,
            default=Decimal('25.00'),
        )
        parser.add_argument(
            '--create-prize-pools',
            action='store_true',
            help='Create empty PaidPrizePool entries for all existing rounds'
        )
        parser.add_argument(
            '--enabled',
            action='store_true',
            default=True,
            help='Enable paid mode immediately'
        )
        parser.add_argument(
            '--disabled',
            action='store_true',
            help='Create config but keep paid mode disabled'
        )
        parser.add_argument(
            '--start-round',
            type=int,
            default=1,
            help='Round number where paid mode starts (default: 1)'
        )

    def handle(self, *args, **options):
        league_slug = options['league_slug']
        round_price = options['round_price']
        league_price = options['league_price']
        platform_fee = options['platform_fee']
        create_prize_pools = options['create_prize_pools']
        is_enabled = not options['disabled']
        start_round = options['start_round']

        try:
            league = League.objects.get(slug=league_slug, state=True)
        except League.DoesNotExist:
            raise CommandError(f'League with slug "{league_slug}" does not exist')

        # Count rounds to calculate league price if not provided
        rounds = Round.objects.filter(league=league, state=True)
        rounds_count = rounds.count()

        if league_price is None:
            # 15% discount for full league
            total_price = round_price * rounds_count
            league_price = total_price * Decimal('0.85')

        self.stdout.write(f'League: {league.name}')
        self.stdout.write(f'Rounds count: {rounds_count}')
        self.stdout.write(f'Round price: ${round_price} ARS')
        self.stdout.write(f'League price: ${league_price} ARS (15% discount)')
        self.stdout.write(f'Platform fee: {platform_fee}%')
        self.stdout.write(f'Start round: {start_round}')
        self.stdout.write(f'Enabled: {is_enabled}')

        with transaction.atomic():
            paid_config, created = PaidLeagueConfig.objects.update_or_create(
                league=league,
                defaults={
                    'is_paid_mode_enabled': is_enabled,
                    'round_price_ars': round_price,
                    'league_price_ars': league_price,
                    'platform_fee_percentage': platform_fee,
                    'start_round_number': start_round,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'Created PaidLeagueConfig for "{league.name}"'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Updated existing PaidLeagueConfig for "{league.name}"'
                ))

            # Create PaidPrizePool entries if requested
            if create_prize_pools:
                prize_pools_created = 0

                # Only create prize pools for rounds >= start_round
                eligible_rounds = rounds.filter(number_round__gte=start_round)
                for round_obj in eligible_rounds:
                    pool, pool_created = PaidPrizePool.objects.get_or_create(
                        league=league,
                        round=round_obj,
                        is_league_pool=False,
                        defaults={
                            'total_pool_ars': Decimal('0.00'),
                            'distributed': False,
                        }
                    )
                    if pool_created:
                        prize_pools_created += 1

                # Create a league-level pool
                league_pool, league_pool_created = PaidPrizePool.objects.get_or_create(
                    league=league,
                    round=None,
                    is_league_pool=True,
                    defaults={
                        'total_pool_ars': Decimal('0.00'),
                        'distributed': False,
                    }
                )
                if league_pool_created:
                    prize_pools_created += 1

                self.stdout.write(self.style.SUCCESS(
                    f'Created {prize_pools_created} PaidPrizePool entries'
                ))

        self.stdout.write(self.style.SUCCESS('Paid league setup complete!'))
        self.stdout.write('Summary:')
        self.stdout.write(f'- League: {league.name} ({league.slug})')
        self.stdout.write(f'- Round Price: ${round_price} ARS')
        self.stdout.write(f'- League Price: ${league_price} ARS')
        self.stdout.write(f'- Platform Fee: {platform_fee}%')
        self.stdout.write(f'- Start Round: {start_round}')
        self.stdout.write(f'- Status: {"Enabled" if is_enabled else "Disabled"}')
        if create_prize_pools:
            eligible_count = rounds.filter(number_round__gte=start_round).count()
            self.stdout.write(
                f'- Prize Pools: {eligible_count} rounds (>= round {start_round}) + 1 league pool'
            )
