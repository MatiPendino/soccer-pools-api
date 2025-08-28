import copy
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from apps.bet.models import BetLeague
from .models import Tournament, TournamentUser
from .serializers import TournamentSerializer, TournamentUserSerializer
from .utils import generate_default_logo, send_tournament_user_notification

logger = logging.getLogger(__name__)
class TournamentViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Tournament.objects.all()

    def create(self, request):
        with transaction.atomic(): 
            user = request.user
            data = copy.copy(request.data)
            data['admin_tournament'] = user.id
            
            league_id = data.get('league', None)
            if league_id is None or league_id == '':
                last_user_visited_league = BetLeague.objects.get_last_visited_bet_league(user)
                league_id = last_user_visited_league.get_league_id()

            data['league'] = int(league_id)
            # If the user does not select a logo, the default logo will be selected
            # In case of an error the logo will be None
            if data['logo'] == 'null':
                try:
                    default_logo = generate_default_logo()
                    data['logo'] = default_logo
                except Exception as e:
                    data['logo'] = None

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            tournament = Tournament.objects.filter(admin_tournament=user).last()
            TournamentUser.objects.create(
                tournament=tournament,
                user=user,
                tournament_user_state=TournamentUser.ACCEPTED
            )
            headers = self.get_success_headers(serializer.data)

            logger.info('Tournament %s created successfully for user %s', tournament.name, user.username)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request):
        """
            Retrieve query param values search_text and league_id
            If search_text is empty, return all the tournaments where the tournaments_user
            states are pending or accepted, and the league_id matches
            If search_text is not empty, return the same tournaments, or tournaments where
            its name contains the search_text, despite they are in the tournaments_user or not
        """
        user = self.request.user
        search_text = self.request.query_params.get('search_text', '')
        league_id = self.request.query_params.get('league_id', '')

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

        serializer = self.get_serializer(tournaments, many=True)
        return Response(serializer.data)


class TournamentUserViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentUserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = TournamentUser.objects.all()

    @action(detail=True, methods=['get'], url_path='pending_tournament_users')
    def pending_tournament_users(self, request, pk=None):
        tournament_id = pk

        tournament_users = TournamentUser.objects.filter(
            state=True,
            tournament__id=tournament_id,
            tournament_user_state=TournamentUser.PENDING
        )

        serializer = self.get_serializer(tournament_users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='update_tournament_user_state')
    def update_tournament_user_state(self, request, pk=None):
        user = request.user
        tournament_user_id = pk
        tournament_state = request.data.get('tournament_state')

        tournament_user = get_object_or_404(TournamentUser, id=tournament_user_id)
        tournament_user.tournament_user_state = tournament_state
        tournament_user.save()
        send_tournament_user_notification(user, tournament_user, tournament_state)

        logger.info(
            'TournamentUser state updated to %s for user %s in tournament %s', 
            TournamentUser.TOURNAMENT_USER_STATES[tournament_state][1], 
            tournament_user.get_user_username(), 
            tournament_user.get_tournament_name()
        )
        serializer = self.get_serializer(tournament_user)
        return Response(serializer.data)




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