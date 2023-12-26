from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Bet

class BetResources(resources.ModelResource):
    class Meta:
        model = Bet

class BetAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('operation_code', 'custom_user__user__username', 'round__name')
    list_display = ('get_custom_user', 'operation_code', 'get_round', 'points', 'winner')
    resource_class = BetResources

    def get_custom_user(self, obj):
        return obj.custom_user
    get_custom_user.admin_order_field = 'custom_user__user__username'
    get_custom_user.short_description = 'User'

    def get_round(self, obj):
        return obj.round
    get_round.admin_order_field = 'round__name'
    get_round.short_description = 'Round'


admin.site.register(Bet, BetAdmin)
