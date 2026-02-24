from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Tournament, TournamentUser


class TournamentResources(resources.ModelResource):
    class Meta:
        model = Tournament

class TournamentAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('name', 'league__name', 'admin_tournament__username', 'admin_tournament__name')
    list_display = ('name', 'get_league_name', 'get_admin_username', 'tournament_type')
    list_filter = ('tournament_type',)
    resource_class = TournamentResources

    def get_league_name(self, obj):
        return obj.league.name
    get_league_name.admin_order_field = 'league__name'
    get_league_name.short_description = 'League'
    
    def get_admin_username(self, obj):
        return obj.admin_tournament.username if obj.admin_tournament else '-'
    get_admin_username.admin_order_field = 'admin_tournament__username'
    get_admin_username.short_description = 'Admin'


class TournamentUserResources(resources.ModelResource):
    class Meta:
        model = TournamentUser

class TournamentUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('tournament__name', 'tournament__league__name', 'user__username', 'user__name')
    list_display = ('get_tournament_name', 'get_user_username', 'get_league_name')
    resource_class = TournamentUserResources

    def get_tournament_name(self, obj):
        return obj.tournament.name
    get_tournament_name.admin_order_field = 'tournament__name'
    get_tournament_name.short_description = 'Tournament'

    def get_user_username(self, obj):
        return obj.user.username
    get_user_username.admin_order_field = 'user__username'
    get_user_username.short_description = 'User'

    def get_league_name(self, obj):
        return obj.tournament.league.name
    get_league_name.admin_order_field = 'tournament__league__name'
    get_league_name.short_description = 'League'


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(TournamentUser, TournamentUserAdmin)