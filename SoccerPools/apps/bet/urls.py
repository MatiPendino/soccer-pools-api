from django.urls import path
from .views import LastFourWinnersView

urlpatterns = [
    path('get_last_four_winners/', LastFourWinnersView.as_view(), name='get_last_four_winners')
]
