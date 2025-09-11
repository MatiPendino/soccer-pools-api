from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from apps.app_user.models import AppUser
from .models import Prize, PrizeUser

class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = ('id', 'title', 'image', 'coins_cost', 'description')


class ClaimPrizeSerializer(serializers.Serializer):
    prize_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context['request']
        user = request.user

        prize = get_object_or_404(Prize, id=attrs['prize_id'], state=True)
        attrs['user'] = user
        attrs['prize'] = prize

        return attrs

    def create(self, validated):
        user = validated['user']
        prize = validated['prize']

        with transaction.atomic():
            # Lock user
            user = AppUser.objects.select_for_update().get(id=user.id)

            if user.coins < prize.coins_cost:
                raise serializers.ValidationError({'Prize': 'Your coins are not enough for the price'})
            
            # Create prize_user and substract user coins
            prize_user = PrizeUser.objects.create(
                user=user,
                prize=prize,
                prize_status=PrizeUser.STARTED
            )

            user.coins = F('coins') - prize.coins_cost
            user.save(update_fields=['coins'])

            return prize_user

