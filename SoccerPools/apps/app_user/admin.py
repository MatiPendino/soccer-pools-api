from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import AppUser, CoinGrant

class AppUserResources(resources.ModelResource):
    class Meta:
        model = AppUser

class AppUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('username', 'name', 'last_name', 'email', 'instagram_username', 'twitter_username')
    list_display = ('username', 'email', 'name', 'last_name', 'coins')
    resource_class = AppUserResources


class CoinGrantResources(resources.ModelResource):
    class Meta:
        model = CoinGrant

class CoinGrantAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('user__username', 'user__email', 'reward_type')
    list_display = ('user', 'reward_type', 'amount', 'creation_date')
    resource_class = CoinGrantResources

admin.site.register(AppUser, AppUserAdmin)
admin.site.register(CoinGrant, CoinGrantAdmin)