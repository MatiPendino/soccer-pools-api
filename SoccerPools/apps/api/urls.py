from django.urls import include, path

urlpatterns = [
    path('user/', include('apps.app_user.urls')),
    path('leagues/', include('apps.league.urls')),
    path('bets/', include('apps.bet.urls')),
    path('matches/', include('apps.match.urls'))
]
