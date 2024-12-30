from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.static import serve
from debug_toolbar.toolbar import debug_toolbar_urls
# from allauth.socialaccount.providers.google.views import oauth2_login, oauth2_callback

urlpatterns = [
    path('soccer_admin/doc/', include('django.contrib.admindocs.urls')),
    path('soccer_admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/', include('djoser.urls.jwt')),
    path('api/', include('apps.api.urls')),
    path('auth/social/', include('djoser.social.urls')),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    })
]
urlpatterns += debug_toolbar_urls()

