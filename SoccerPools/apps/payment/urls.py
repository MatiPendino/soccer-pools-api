from django.urls import path
from .views import (
    PaidLeagueListView, CreateRoundPaymentView, CreateLeaguePaymentView, PaymentStatusView,
    MercadoPagoWebhookView, UserPaymentHistoryView, UserPaidBetRoundsView,
    PaidBetRoundDetailView, UpdatePaidMatchResultView, BulkUpdatePaidMatchResultsView, 
    RoundLeaderboardView, LeagueLeaderboardView, RoundPrizePoolView,
)

urlpatterns = [
    path('round/<int:round_id>/pay/', CreateRoundPaymentView.as_view(), name='create_round_payment'),
    path('league/<slug:league_slug>/pay/', CreateLeaguePaymentView.as_view(), name='create_league_payment'),
    path('status/<str:external_ref>/', PaymentStatusView.as_view(), name='payment_status'),
    path('webhook/mercadopago/', MercadoPagoWebhookView.as_view(), name='mercadopago_webhook'),
    path('leagues/', PaidLeagueListView.as_view(), name='paid_leagues_list'),
    path('history/', UserPaymentHistoryView.as_view(), name='payment_history'),
    path('bets/', UserPaidBetRoundsView.as_view(), name='user_paid_bets'),
    path('bets/<int:pk>/', PaidBetRoundDetailView.as_view(), name='paid_bet_detail'),
    path('predictions/<int:match_result_id>/', UpdatePaidMatchResultView.as_view(), name='update_prediction'),
    path('predictions/bulk/<int:paid_bet_round_id>/', BulkUpdatePaidMatchResultsView.as_view(), name='bulk_update_predictions'),
    path('leaderboard/round/<slug:round_slug>/', RoundLeaderboardView.as_view(), name='round_leaderboard'),
    path('leaderboard/league/<slug:league_slug>/', LeagueLeaderboardView.as_view(), name='league_leaderboard'),
    path('prize-pool/round/<slug:round_slug>/', RoundPrizePoolView.as_view(), name='round_prize_pool'),
]
