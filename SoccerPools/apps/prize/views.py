from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from django.db import transaction
from .serializers import PrizeSerializer, ClaimPrizeSerializer
from .models import Prize
from .tasks import send_prize_request_email_task

class PrizeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PrizeSerializer
    permission_classes = [AllowAny]
    queryset = Prize.objects.filter(state=True)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def claim(self, request, pk=None):
        serializer = ClaimPrizeSerializer(data={'prize_id': pk}, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        transaction.on_commit(lambda: send_prize_request_email_task(user_id=request.user.id, prize_id=pk))

        return Response(
            {'success' : 'Prize claimed successfully! We will get in touch in the next 24hs'}, 
            status=status.HTTP_201_CREATED
        )
