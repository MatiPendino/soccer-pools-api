import random
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.app_user.models import AppUser
from apps.league.models import Round
from apps.match.models import MatchResult
from apps.payment.models import Payment, PaidBetRound, PaidLeagueConfig
from apps.payment.services import calculate_payment_amounts, process_approved_payment

class Command(BaseCommand):
    help = 'Simulate a user paying for a round (for testing/development purposes)'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user'
        )
        parser.add_argument(
            'round_slug',
            type=str,
            help='Slug of the round'
        )
        parser.add_argument(
            '--skip-validations',
            action='store_true',
            help='Skip round state checks (allow started rounds)'
        )
        parser.add_argument(
            '--random-predictions',
            action='store_true',
            help='Generate random match predictions (0-2 goals)'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['pending', 'approved'],
            default='approved',
            help='Payment status (default: approved)'
        )

    def handle(self, *args, **options):
        username = options['username']
        round_slug = options['round_slug']
        skip_validations = options['skip_validations']
        random_predictions = options['random_predictions']
        payment_status = options['status']

        # Validate user exists
        try:
            user = AppUser.objects.get(username=username)
            self.stdout.write(f'User found: {user.username} ({user.email})')
        except AppUser.DoesNotExist:
            raise CommandError(f'User with username "{username}" does not exist')

        # Validate round exists
        try:
            round_obj = Round.objects.get(slug=round_slug, state=True)
            self.stdout.write(f'Round found: {round_obj.name} (League: {round_obj.league.name})')
        except Round.DoesNotExist:
            raise CommandError(f'Round with slug "{round_slug}" does not exist')

        # Validate paid mode is enabled
        try:
            config = PaidLeagueConfig.objects.get(league=round_obj.league, state=True)
            if not config.is_paid_mode_enabled:
                raise CommandError(f'Paid mode is disabled for league "{round_obj.league.name}"')

            self.stdout.write(
                f'Paid config found: ${config.round_price_ars} ARS per round '
                f'({config.platform_fee_percentage}% platform fee)'
            )
        except PaidLeagueConfig.DoesNotExist:
            raise CommandError(f'Paid mode is not configured for league "{round_obj.league.name}"')

        # Check for duplicate payment
        if PaidBetRound.objects.filter(user=user, round=round_obj, state=True).exists():
            raise CommandError(
                f'User "{username}" already has a paid bet for round "{round_obj.name}"'
            )

        # Validate round state (unless skip_validations)
        if not skip_validations:
            if round_obj.round_state != Round.NOT_STARTED_ROUND:
                raise CommandError(
                    f'Round "{round_obj.name}" has already started '
                    f'(state: {round_obj.round_state}). Use --skip-validations to bypass.'
                )

        # Calculate payment amounts
        gross_amount = config.round_price_ars
        amounts = calculate_payment_amounts(gross_amount, config.platform_fee_percentage)

        self.stdout.write('Payment breakdown:')
        self.stdout.write(f'Gross amount: ${gross_amount} ARS')
        self.stdout.write(
            f'Platform fee ({config.platform_fee_percentage}%): ${amounts["platform_fee"]} ARS'
        )
        self.stdout.write(f'Prize pool contribution: ${amounts["prize_pool"]} ARS')

        # Create payment and process it
        try:
            with transaction.atomic():
                payment = Payment.objects.create(
                    user=user,
                    payment_type=Payment.PAYMENT_TYPE_ROUND,
                    status=payment_status,
                    gross_amount_ars=gross_amount,
                    platform_fee_ars=amounts['platform_fee'],
                    prize_pool_ars=amounts['prize_pool'],
                    league=round_obj.league,
                    round=round_obj,
                    mp_preference_id=f'test_pref_{username}_{round_slug}',
                    mp_payment_id=f'test_pay_{username}_{round_slug}',
                )

                self.stdout.write(
                    f'Payment created: ID={payment.id}, external_ref={payment.external_reference}'
                )

                # Process payment if approved
                if payment.status == Payment.STATUS_APPROVED:
                    success = process_approved_payment(payment)
                    if not success:
                        raise CommandError('Failed to process approved payment')

                    # Get the created PaidBetRound
                    paid_bet_round = PaidBetRound.objects.get(
                        user=user,
                        round=round_obj,
                        state=True
                    )

                    match_results = MatchResult.objects.filter(
                        paid_bet_round=paid_bet_round,
                        state=True
                    )

                    self.stdout.write(self.style.SUCCESS('Payment processed successfully! Created:'))
                    self.stdout.write(f'- PaidBetRound (ID: {paid_bet_round.id})')
                    self.stdout.write(f'- BetLeague (auto-registered)')
                    self.stdout.write(f'- BetRound')
                    self.stdout.write(f'- {match_results.count()} MatchResult records')
                    self.stdout.write(f'- Prize pool updated')

                    # Generate random predictions if requested
                    if random_predictions and match_results.exists():
                        for mr in match_results:
                            mr.goals_team_1 = random.randint(0, 2)
                            mr.goals_team_2 = random.randint(0, 2)
                            mr.save()

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Generated random predictions for {match_results.count()} matches'
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Payment created with status "{payment_status}". '
                            'Bet records will be created when payment is approved.'
                        )
                    )

        except Exception as e:
            raise CommandError(f'Error creating payment: {str(e)}')

        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Simulation complete!'))
        self.stdout.write('Summary:')
        self.stdout.write(f'  User: {user.username}')
        self.stdout.write(f'  Round: {round_obj.name}')
        self.stdout.write(f'  Payment: ${gross_amount} ARS')
        self.stdout.write(f'  Status: {payment_status.capitalize()}')
