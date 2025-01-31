from django.urls import path
from .views import *

urlpatterns = [
    path('league/', LeagueListApiView.as_view(), name='league_list'),
    path('league/<int:pk>/', LeagueRetrieveApiView.as_view(), name='league_retrieve'),
    path('round/<int:pk>/', RoundRetrieveApiView.as_view(), name='round_retrieve'),
    path('rounds/league/<int:pk>/', RoundListApiView.as_view(), name='rounds_league'),
    path('team/', TeamListApiView.as_view(), name='team_list'),
    path('team/<int:pk>/', TeamRetrieveApiView.as_view(), name='team_retrieve'),
]