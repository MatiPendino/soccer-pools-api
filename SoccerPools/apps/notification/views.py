from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions, status
from django.db import transaction
from apps.bet.models import BetLeague
from .models import FCMToken
from .serializers import FCMTokenSerializer

class FCMTokenAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
            Create or retrieve FCMToken and add corresponding Leagues
            Return FCMToken serialized object
        """
        token = request.data.get('fcm_token')
        user = request.user
        leagues = BetLeague.objects.filter(state=True, user=user).values_list('league', flat=True)

        with transaction.atomic():
            fcm_token, was_created = FCMToken.objects.get_or_create(
                token_id=token,
                user=user,
            )
            if leagues:
                fcm_token.leagues.add(*leagues)

        fcm_serializer = FCMTokenSerializer(fcm_token)

        return Response(
            fcm_serializer.data, 
            status=status.HTTP_201_CREATED if was_created else status.HTTP_200_OK
        )