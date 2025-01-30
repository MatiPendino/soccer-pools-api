from django.urls import path
from .views import BetResultsApiView, LeagueBetsMatchResultsCreateApiView

urlpatterns = [
    path('bet_results/', BetResultsApiView.as_view(), name='bet_results'),
    path('league_bets_create/', LeagueBetsMatchResultsCreateApiView.as_view(), name='league_bets_create'),
]
