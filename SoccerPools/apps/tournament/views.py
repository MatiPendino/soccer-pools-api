import copy
import logging
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Case, When, IntegerField
from apps.bet.models import BetLeague
from .models import Tournament, TournamentUser
from .serializers import TournamentSerializer, TournamentUserSerializer
from .pagination import TournamentPagination
from .utils import generate_default_logo, send_tournament_user_notification

logger = logging.getLogger(__name__)
class TournamentViewSet(viewsets.ModelViewSet):
    serializer_class = TournamentSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Tournament.objects.all()
    pagination_class = TournamentPagination

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
        user = request.user
        search_text = request.query_params.get('search_text', '')
        league_id = request.query_params.get('league_id', '')

        if not league_id:
            return Response(
                {'detail': 'league_id is required'}, status=status.HTTP_400_BAD_REQUEST
            )

        # IDs of tournaments where the user is PENDING or ACCEPTED
        user_tournament_ids = list(
            TournamentUser.objects.filter(
                Q(tournament_user_state=TournamentUser.PENDING) |
                Q(tournament_user_state=TournamentUser.ACCEPTED),
                state=True,
                user=user
            ).values_list('tournament_id', flat=True)
        )
        tournaments = Tournament.objects.filter(
            state=True,
            league__id=league_id
        ).annotate(
            participants_count=Count(
                'tournamentuser',
                filter=Q(
                    tournamentuser__state=True,
                    tournamentuser__tournament_user_state=TournamentUser.ACCEPTED
                )
            ),
            is_user_member=Case(
                When(id__in=user_tournament_ids, then=0),
                default=1,
                output_field=IntegerField()
            )
        ).order_by('is_user_member', '-participants_count', 'name')

        if search_text:
            tournaments = tournaments.filter(name__icontains=search_text)

        page = self.paginate_queryset(tournaments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tournaments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='join')
    def join(self, request, pk=None):
        """Join a tournament"""
        user = request.user
        tournament = get_object_or_404(Tournament, id=pk, state=True)

        existing = TournamentUser.objects.filter(
            tournament=tournament, user=user, state=True
        ).first()
        if existing:
            return Response(
                {'detail': 'Already requested or joined this tournament.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tournament.tournament_type == Tournament.PUBLIC:
            tournament_user = TournamentUser.objects.create(
                tournament=tournament,
                user=user,
                tournament_user_state=TournamentUser.ACCEPTED
            )
            logger.info('User %s joined PUBLIC tournament %s', user.username, tournament.name)
        else:
            tournament_user = TournamentUser.objects.create(
                tournament=tournament,
                user=user,
                tournament_user_state=TournamentUser.PENDING
            )
            send_tournament_user_notification(user, tournament_user, TournamentUser.PENDING)
            logger.info(
                'User %s requested to join PRIVATE tournament %s', user.username, tournament.name
            )

        serializer = TournamentUserSerializer(tournament_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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