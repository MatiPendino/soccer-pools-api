from django.urls import path
from .views import *

urlpatterns = [
    path('league/', LeagueListApiView.as_view(), name='league_list'),
    path('league/<int:pk>/', LeagueRetrieveApiView.as_view(), name='league_retrieve'),
    path('next_rounds/', NextRoundsListApiView.as_view(), name='next_rounds'),
    path('current_rounds/', CurrentRoundsListApiView.as_view(), name='current_rounds'),
    path('expired_rounds/', ExpiredRoundsListApiView.as_view(), name='expired_rounds'),
    path('round/<int:pk>/', RoundRetrieveApiView.as_view(), name='round_retrieve'),
    path('team/', TeamListApiView.as_view(), name='team_list'),
    path('team/<int:pk>/', TeamRetrieveApiView.as_view(), name='team_retrieve'),
]