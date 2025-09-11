from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import Prize, PrizeUser

class PrizeResources(resources.ModelResource):
    class Meta:
        model = Prize

class PrizeAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = PrizeResources
    list_display = ('id', 'title', 'coins_cost')
    search_fields = ('id', 'title')


class PrizeUserResources(resources.ModelResource):
    class Meta:
        model = PrizeUser

class PrizeUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = PrizeUserResources
    list_display = ('id', 'get_user_username', 'get_prize_title')
    search_fields = ('user__username', 'user__email', 'user__name', 'user__last_name', 'prize__title')

    def get_user_username(self, obj):
        return obj.user.username
    get_user_username.short_description = 'User'
    get_user_username.admin_order_field = 'user__username'

    def get_prize_title(self, obj):
        return obj.prize.title
    get_prize_title.short_description = 'Prize'
    get_prize_title.admin_order_field = 'prize__title'

admin.site.register(Prize, PrizeAdmin)
admin.site.register(PrizeUser, PrizeUserAdmin)