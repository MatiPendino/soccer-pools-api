from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.static import serve
from apps.league import urls as league_urls
from apps.app_user import urls as user_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include(user_urls)),
    path('leagues/', include(league_urls)),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    })
]

