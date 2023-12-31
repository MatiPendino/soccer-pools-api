from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Bet

class BetResources(resources.ModelResource):
    class Meta:
        model = Bet

class BetAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('operation_code', 'user__username', 'round__name')
    list_display = ('get_user', 'operation_code', 'get_round', 'points', 'winner')
    resource_class = BetResources

    def get_user(self, obj):
        return obj.user
    get_user.admin_order_field = 'user__username'
    get_user.short_description = 'User'

    def get_round(self, obj):
        return obj.round
    get_round.admin_order_field = 'round__name'
    get_round.short_description = 'Round'


admin.site.register(Bet, BetAdmin)
