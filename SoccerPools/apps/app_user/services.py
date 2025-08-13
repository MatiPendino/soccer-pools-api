from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import AppUser, CoinGrant

def grant_coins(user, reward_type, coins):
    """Grants coins to the user based on the reward type"""
    today = timezone.localdate()

    with transaction.atomic():
        # Lock user row to avoid race conditions on balance
        user = AppUser.objects.select_for_update().get(pk=user.pk)

        if reward_type == CoinGrant.AD_REWARD:
            today_count = CoinGrant.objects.filter(
                user=user, reward_type=CoinGrant.AD_REWARD, creation_date=today
            ).count()
            if today_count >= CoinGrant.AD_REWARD_DAILY_CAP:
                raise ValidationError({'daily_ad_limit': 'Daily ad limit reached'})

        elif reward_type == CoinGrant.APP_REVIEW:
            if CoinGrant.objects.filter(user=user, reward_type=CoinGrant.APP_REVIEW).exists():
                raise ValidationError({'existing_app_review': 'You have already received the app review reward'})
            
        CoinGrant.objects.create(
            user=user,
            reward_type=reward_type,
            amount=coins,
            description=f'Added {coins} coins for {CoinGrant.REWARD_TYPES[reward_type][1]}'
        )

        user.coins = F('coins') + coins
        user.save()
    
    user.refresh_from_db(fields=['coins'])
    return user.coins