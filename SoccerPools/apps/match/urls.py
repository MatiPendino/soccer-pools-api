from django.urls import path
from .views import *

urlpatterns = [
    path('match_results/', MatchResultsListCreateApiView.as_view(), name='match_results'),
]
