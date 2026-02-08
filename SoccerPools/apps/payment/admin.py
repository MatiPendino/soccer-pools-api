from django.contrib import admin
from django.utils.html import format_html
from .models import PaidLeagueConfig, Payment, PaidBetRound, PaidPrizePool, PaidWinner

@admin.register(PaidLeagueConfig)
class PaidLeagueConfigAdmin(admin.ModelAdmin):
    list_display = (
        'league', 'round_price_ars', 'league_price_ars', 'state',
    )
    list_filter = ('state',)
    search_fields = ('league__name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'payment_type', 'status_badge', 'gross_amount_ars',
        'league', 'round', 'creation_date',
    )
    list_filter = ('status', 'payment_type', 'creation_date')
    search_fields = (
        'user__username', 'user__email', 'external_reference', 'mp_payment_id',
    )
    readonly_fields = (
        'external_reference', 'mp_preference_id', 'mp_payment_id', 'creation_date',
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'approved': '#28A745',
            'rejected': '#DC3545',
            'cancelled': '#6C757D',
            'refunded': '#17A2B8',
        }
        color = colors.get(obj.status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(PaidBetRound)
class PaidBetRoundAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'round', 'winner_first', 'winner_second', 'winner_third',
    )
    list_filter = ('winner_first', 'winner_second', 'winner_third', 'state')
    search_fields = ('user__username', 'round__name')


@admin.register(PaidPrizePool)
class PaidPrizePoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'league', 'round', 'total_pool_ars', 'distributed',)
    list_filter = ('distributed',)
    search_fields = ('league__name', 'round__name')


@admin.register(PaidWinner)
class PaidWinnerAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_user_email', 'prize_amount_ars', 'contact_status_badge', 'get_round',
    )
    list_filter = ('position', 'contact_status')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'prize_pool', 'position', 'prize_amount_ars')
    actions = ['mark_as_contacted', 'mark_as_paid']

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

    def get_round(self, obj):
        if obj.prize_pool.round:
            return obj.prize_pool.round.name
        return '-'
    get_round.short_description = 'Round'

    def position_badge(self, obj):
        colors = {1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32'}
        color = colors.get(obj.position, '#6C757D')
        position_name = {1: '1st', 2: '2nd', 3: '3rd'}.get(obj.position, f'{obj.position}th')
        return format_html(
            '<span style="background-color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            position_name
        )
    position_badge.short_description = 'Position'

    def contact_status_badge(self, obj):
        colors = {
            PaidWinner.CONTACT_STATUS_PENDING: '#FFA500',
            PaidWinner.CONTACT_STATUS_CONTACTED: '#17A2B8',
            PaidWinner.CONTACT_STATUS_PAID: '#28A745',
        }
        color = colors.get(obj.contact_status, '#6C757D')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color,
            obj.get_contact_status_display()
        )
    contact_status_badge.short_description = 'Contact Status'

    @admin.action(description='Mark selected winners as Contacted')
    def mark_as_contacted(self, request, queryset):
        updated = queryset.update(contact_status=PaidWinner.CONTACT_STATUS_CONTACTED)
        self.message_user(request, f'{updated} winner(s) marked as contacted.')

    @admin.action(description='Mark selected winners as Paid')
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(contact_status=PaidWinner.CONTACT_STATUS_PAID)
        self.message_user(request, f'{updated} winner(s) marked as paid.')
