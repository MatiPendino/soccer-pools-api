from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Match, MatchResult

class MatchResources(resources.ModelResource):
    class Meta:
        model = Match

class MatchAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('id', 'team_1__name', 'team_2__name', 'round__name', 'round__league__name')
    list_display = ('id', 'get_round_name', 'get_team_1', 'get_team_2', 'get_league_name')
    resource_class = MatchResources


    def get_team_1(self, obj):
        return obj.team_1.name
    get_team_1.admin_order_field = 'team_1__name'
    get_team_1.short_description = 'Team 1'

    def get_team_2(self, obj):
        return obj.team_2.name
    get_team_2.admin_order_field = 'team_2__name'
    get_team_2.short_description = 'Team 2'

    def get_round_name(self, obj):
        return obj.round.name
    get_round_name.admin_order_field = 'round__name'
    get_round_name.short_description = 'Round'

    def get_league_name(self, obj):
        return obj.round.league.name
    get_league_name.admin_order_field = 'round__league__name'
    get_league_name.short_description = 'League'

admin.site.register(Match, MatchAdmin)


class MatchResultResources(resources.ModelResource):
    class Meta:
        model = MatchResult

class MatchResultAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('match__team_1__name', 'match__team_2__name', 'match__round__name', 'match__round__league__name')
    list_display = ('get_round_name', 'get_user_username', 'get_team_1', 'goals_team_1', 'get_team_2', 'goals_team_2', 'original_result', 'get_league_name',)
    resource_class = MatchResultResources

    def get_team_1(self, obj):
        return obj.match.team_1.name
    get_team_1.admin_order_field = 'match__team_1__name'
    get_team_1.short_description = 'Team 1'

    def get_team_2(self, obj):
        return obj.match.team_2.name
    get_team_2.admin_order_field = 'match__team_2__name'
    get_team_2.short_description = 'Team 2'

    def get_round_name(self, obj):
        return obj.match.round.name
    get_round_name.admin_order_field = 'match__round__name'
    get_round_name.short_description = 'Round'

    def get_league_name(self, obj):
        return obj.match.round.league.name
    get_league_name.admin_order_field = 'match__round__league__name'
    get_league_name.short_description = 'League'

    def get_user_username(self, obj):
        return obj.bet_round.user.username if obj.bet_round else 'admin'
    get_user_username.admin_order_field = 'bet_round__user__username'
    get_user_username.short_description = 'User'

admin.site.register(MatchResult, MatchResultAdmin)