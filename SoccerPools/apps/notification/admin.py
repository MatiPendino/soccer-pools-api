from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from .models import FCMToken

class FCMTokenResources(resources.ModelResource):
    class Meta:
        model = FCMToken

class FCMTokenAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('token_id', 'user__username', 'user__name', 'user__last_name')
    list_display = ('get_username', 'token_id', 'state')
    resource_class = FCMTokenResources

    def get_username(self, obj):
        return obj.user.username
    get_username.admin_order_field = 'user__username'
    get_username.short_description = 'User'

admin.site.register(FCMToken, FCMTokenAdmin)