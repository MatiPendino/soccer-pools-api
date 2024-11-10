from django.urls import path
from .views import MatchResultsCreateApiView

urlpatterns = [
    path('match_results/', MatchResultsCreateApiView.as_view(), name='match_results'),
]
