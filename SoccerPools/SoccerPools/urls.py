from django.contrib import admin
from django.urls import path, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    })
]

