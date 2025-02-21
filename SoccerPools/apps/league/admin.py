from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import League, Team, Round

class LeagueResources(resources.ModelResource):
    class Meta:
        model = League

class LeagueAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('name', 'slug')
    list_display = ('name', 'slug')
    resource_class = LeagueResources

admin.site.register(League, LeagueAdmin)


class RoundResources(resources.ModelResource):
    class Meta:
        model = Round

class RoundAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('name', 'league__name', 'slug')
    list_display = ('name', 'get_league_name', 'slug', 'round_state', 'pool')
    resource_class = RoundResources

    def get_league_name(self, obj):
        return obj.league.name
    get_league_name.admin_order_field = 'league__name'
    get_league_name.short_description = 'League'

admin.site.register(Round, RoundAdmin)


class TeamResources(resources.ModelResource):
    class Meta:
        model = Team

class TeamAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('name', 'slug', 'league__name')
    list_display = ('name', 'get_league_name', 'slug')
    resource_class = TeamResources

    def get_league_name(self, obj):
        return obj.league.name
    get_league_name.admin_order_field = 'league__name'
    get_league_name.short_description = 'League'

admin.site.register(Team, TeamAdmin)