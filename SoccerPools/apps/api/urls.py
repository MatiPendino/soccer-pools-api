from django.urls import include, path
from apps.league import urls as league_urls
from apps.app_user import urls as user_urls
from apps.bet import urls as bet_urls

urlpatterns = [
    path('user/', include('apps.app_user.urls')),
    path('leagues/', include('apps.league.urls')),
    path('bets/', include('apps.bet.urls')),
    path('matches/', include('apps.match.urls'))
]
