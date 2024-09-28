from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from .serializers import BetSerializer
from .models import Bet

class LastFourWinnersView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BetSerializer

    def get_queryset(self):
        winner_bets = Bet.objects.filter(winner=True).order_by('-updating_date')[:4]
        return winner_bets


