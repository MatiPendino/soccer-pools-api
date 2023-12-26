from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser

class CustomUserResources(resources.ModelResource):
    class Meta:
        model = CustomUser

class CustomUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    list_display = ('get_username', 'get_email', 'get_first_name', 'get_last_name')
    resource_class = CustomUserResources

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.short_description = 'First name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.short_description = 'Last name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

admin.site.register(CustomUser, CustomUserAdmin)