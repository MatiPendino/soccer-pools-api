from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'user', UserViewSet)

urlpatterns = [
    path('user_destroy/', UserDestroyApiView.as_view(), name='user_destroy'),
    path('user_in_league/', UserInLeague.as_view(), name='user_in_league'),
    path('user_league/', LeagueUser.as_view(), name='league_users'),
    path('user_editable/', UserEditable.as_view(), name='user_editable'),
    path('user_coins/', UserCoinsView.as_view(), name='user_coins'),
    path('avatars/', AvatarListView.as_view(), name='avatars'),
    path('android_google_oauth2/', GoogleLoginView.as_view(), name='android-google-oauth2'),
    path('remove_user/', remove_user, name='remove_user'),
    path('activate/<uid>/<token>/', activate_user, name='activate-user'),
    path('password_reset_confirm/<uid>/<token>/', password_reset_confirm_view, name="password-reset-confirm"),
]

urlpatterns += router.urls