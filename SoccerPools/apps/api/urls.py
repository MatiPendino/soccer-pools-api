from django.urls import include, path

urlpatterns = [
    path('user/', include('apps.app_user.urls')),
    path('leagues/', include('apps.league.urls')),
    path('bets/', include('apps.bet.urls')),
    path('matches/', include('apps.match.urls')),
    path('notifications/', include('apps.notification.urls')),
    path('tournaments/', include('apps.tournament.urls')),
    path('prizes/', include('apps.prize.urls')),
    path('payments/', include('apps.payment.urls')),
]
