from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import AppUser

class AppUserResources(resources.ModelResource):
    class Meta:
        model = AppUser

class AppUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ('username', 'name', 'last_name', 'email')
    list_display = ('username', 'email', 'name', 'last_name')
    resource_class = AppUserResources

admin.site.register(AppUser, AppUserAdmin)