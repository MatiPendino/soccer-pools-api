from django.urls import path
from .views import LastFourWinnersView, BetCreateApiView, LeagueBetsMatchResultsCreateApiView

urlpatterns = [
    path('get_last_four_winners/', LastFourWinnersView.as_view(), name='get_last_four_winners'),
    path('bet_create/', BetCreateApiView.as_view(), name='bet_create'),
    path('league_bets_create/', LeagueBetsMatchResultsCreateApiView.as_view(), name='league_bets_create'),
]
