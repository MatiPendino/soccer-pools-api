from rest_framework.routers import SimpleRouter
from django.urls import path
from .views import *

router = SimpleRouter()
router.register(r'tournament', TournamentViewSet)
router.register(r'tournament_user', TournamentUserViewSet)

urlpatterns = [
    path('tournament_user_tnt_id/<int:tournament_id>/', TournamentUserTournamentIdAPIView.as_view(), name='tournament_user_id'),
]

urlpatterns += router.urls