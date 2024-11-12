from django.urls import path
from .views import UserRegister, UserLogin, UserLogout, UserView, UserInLeague

urlpatterns = [
    path('register/', UserRegister.as_view(), name='user_register'),
    path('login/', UserLogin.as_view(), name='user_login'),
    path('logout/', UserLogout.as_view(), name='user_logout'),
    path('user/', UserView.as_view(), name='user_view'),
    path('user_in_league/', UserInLeague.as_view(), name='user_in_league'),
]
