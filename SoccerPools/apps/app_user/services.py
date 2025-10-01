import requests
import logging
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.files.base import ContentFile
from .models import AppUser, CoinGrant

logger = logging.getLogger(__name__)

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


def add_google_picture_app_user(user, google_picture_url):
    response = requests.get(google_picture_url)
    if response.status_code == status.HTTP_200_OK:
        image_file = ContentFile(response.content)
        user.profile_image.save(f'{user.username}_profile.jpg', image_file)
        user.save(update_fields=['profile_image'])
    

def referral_signup(user, referral_code):
    """Handles the referral signup process"""
    try:
        # Add referred_by and coins to the referred user
        referrer = AppUser.objects.get(referral_code=referral_code)
        user.referred_by = referrer
        user.coins = F('coins') + CoinGrant.REFERRAL_SIGNUP_AMOUNT
        user.save(update_fields=['referred_by', 'coins'])
        logger.info('User %s referred by %s', user.username, referrer.username)

        # Grant coins to the referrer for the referral signup
        grant_coins(
            user=referrer, 
            reward_type=CoinGrant.REFERRAL_SIGNUP, 
            coins=CoinGrant.REFERRAL_SIGNUP_AMOUNT
        )
        logger.info(
            'Granted %s coins to referrer %s for referral signup', 
            CoinGrant.REFERRAL_SIGNUP_AMOUNT, 
            referrer.username
        )
    except AppUser.DoesNotExist:
        logger.warning('Invalid referral code provided: %s', referral_code)