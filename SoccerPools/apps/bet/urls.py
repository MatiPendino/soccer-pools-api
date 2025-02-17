from django.urls import path
from .views import BetRoundResultsApiView, LeagueBetRoundsMatchResultsCreateApiView

urlpatterns = [
    path('bet_results/<slug:round_slug>/<int:tournament_id>/', BetRoundResultsApiView.as_view(), name='bet_results'),
    path('league_bets_create/', LeagueBetRoundsMatchResultsCreateApiView.as_view(), name='league_bets_create'),
]
