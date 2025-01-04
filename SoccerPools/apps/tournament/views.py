from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Tournament, TournamentUser
from .serializers import TournamentSerializer, TournamentUserSerializer

class TournamentViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Tournament.objects.all()

    def get_queryset(self):
        """
            Retrieve query param values search_text and league_id
            If search_text is empty, return all the tournaments where the tournaments_user
            states are pending or accepted, and the league_id matches
            If search_text is not empty, return the same tournaments, or tournaments where
            its name contains the search_text, despite they are in the tournaments_user or not
        """
        user = self.request.user
        search_text = self.request.query_params.get('search_text')
        league_id = self.request.query_params.get('league_id')

        tournaments_user = TournamentUser.objects.filter(
            Q(tournament_user_state=TournamentUser.PENDING) |
            Q(tournament_user_state=TournamentUser.ACCEPTED),
            state=True,
            user=user
        )
        tournaments = Tournament.objects.filter(
            state=True,
            league__id=league_id
        )
        if search_text == '':
            tournaments = tournaments.filter(
                id__in=tournaments_user.values('tournament'),
            )
        else:
            tournaments = tournaments.filter(
                Q(id__in=tournaments_user.values('tournament')) |
                Q(name__icontains=search_text),
            )

        return tournaments


class TournamentUserViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = TournamentUser.objects.all()


class TournamentUserTournamentIdAPIView(APIView):
    """
        Returns the TournamentUser object for the user and tournament_id indicated
        using the TournamentUserSerializer. If there is no TournamentUser record yet, it creates one
    """
    permission_classes = (permissions.IsAuthenticated,)
    def get(self, request, tournament_id):
        user = request.user

        tournament = get_object_or_404(Tournament, id=tournament_id)
        tournament_user, created = TournamentUser.objects.get_or_create(user=user, tournament=tournament)

        serializer = TournamentUserSerializer(tournament_user)

        return Response(serializer.data, status=status.HTTP_200_OK)