from django.urls import path
from .views import *

urlpatterns = [
    path('bet_results/<slug:round_slug>/<int:tournament_id>/', BetRoundResultsLegacyApiView.as_view(), name='bet_results_legacy'),
    path('bet_results/v2/<slug:round_slug>/<int:tournament_id>/', BetRoundResultsApiView.as_view(), name='bet_results'),
    path('league_bets_create/', LeagueBetRoundsMatchResultsCreateApiView.as_view(), name='league_bets_create'),
]
