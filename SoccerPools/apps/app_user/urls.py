from django.urls import path
from .views import *

urlpatterns = [
    path('register/', UserRegister.as_view(), name='user_register'),
    path('login/', UserLogin.as_view(), name='user_login'),
    path('logout/', UserLogout.as_view(), name='user_logout'),
    path('user/', UserView.as_view(), name='user_view'),
    path('user_in_league/', UserInLeague.as_view(), name='user_in_league'),
    path('user_league/', LeagueUser.as_view(), name='league_users'),
]
