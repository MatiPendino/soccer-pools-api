from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import BetRound, BetLeague

class BetLeagueResources(resources.ModelResource):
    class Meta:
        model = BetLeague

class BetLeagueAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('operation_code', 'user__username', 'league__name')
    list_display = ('get_user', 'operation_code', 'get_league')
    resource_class = BetLeagueResources

    def get_user(self, obj):
        return obj.user
    get_user.admin_order_field = 'user__username'
    get_user.short_description = 'User'

    def get_league(self, obj):
        return obj.league
    get_league.admin_order_field = 'league__name'
    get_league.short_description = 'League'


class BetRoundResources(resources.ModelResource):
    class Meta:
        model = BetRound

class BetRoundAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('operation_code', 'bet_league__user__username', 'round__name')
    list_display = ('get_user_username', 'operation_code', 'get_round', 'points')
    resource_class = BetRoundResources

    def get_user_username(self, obj):
        return obj.bet_league.get_user_username() if obj.bet_league else '-'
    get_user_username.admin_order_field = 'bet_league__user__username'
    get_user_username.short_description = 'User'

    def get_round(self, obj):
        return obj.round
    get_round.admin_order_field = 'round__name'
    get_round.short_description = 'Round'


admin.site.register(BetLeague, BetLeagueAdmin)
admin.site.register(BetRound, BetRoundAdmin)
