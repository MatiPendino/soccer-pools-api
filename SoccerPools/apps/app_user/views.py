import requests
import logging
from decouple import config
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView, RetrieveAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, NotFound
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.shortcuts import render
from utils import generate_unique_field_value
from apps.bet.models import BetLeague
from apps.league.serializers import LeagueSerializer
from .models import AppUser, CoinGrant, Avatar
from .serializers import (
    UserSerializer, AddCoinsSerializer, UserEditableSerializer, UserCoinsSerializer,
    UserMemberSerializer, AvatarSerializer
)
from .services import grant_coins, add_google_picture_app_user, referral_signup

logger = logging.getLogger(__name__)
 
class UserViewSet(ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = AppUser.objects.all()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Get the current user"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['post'], url_path='add_coins')
    def add_coins(self, request):
        """Add coins to the user"""
        serializer = AddCoinsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reward_type = serializer.validated_data['reward_type']
        coins = serializer.validated_data['coins']
        new_balance = grant_coins(user=request.user, reward_type=reward_type, coins=coins)
        logger.info(
            'Granted %s coins to user %s for %s', 
            coins, request.user.id, CoinGrant.REWARD_TYPES[reward_type][1]
        )

        return Response({'coins': new_balance}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='members')
    def members(self, request):
        user = request.user
        members = AppUser.objects.filter(referred_by=user)

        return Response(UserMemberSerializer(members, many=True).data, status=status.HTTP_200_OK)
    

class UserDestroyApiView(APIView):
    """
        The User, and all their bets and match results will be logically removed
    """
    def delete(self, request, *args, **kwargs):
        user = request.user

        if not user or not user.is_authenticated:
            raise NotFound('User not found or not authenticated')

        logger.info('User %s requested account deletion', user.username)
        user.remove_user()
        return Response({'success': 'User removed successfully'}, status=status.HTTP_204_NO_CONTENT)


class UserInLeague(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        """
            If the user is in at least one league returns True, otherwise False

            in_league: Bool
        """
        if BetLeague.objects.filter(user=request.user, state=True).exists():
            return Response({'in_league': True})
        
        return Response({'in_league': False})
    

class LeagueUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """Gets the League based on the User"""
        user = request.user
        bet_league = BetLeague.objects.get_last_visited_bet_league(user)
        league = bet_league.league
        league_serializer = LeagueSerializer(league)

        return Response(league_serializer.data)
    

class UserEditable(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserEditableSerializer
    parser_classes = [MultiPartParser, FormParser]  # Enable image upload

    def get_object(self):
        return self.request.user
    
    def perform_update(self, serializer):
        user = serializer.save()
        logger.info('Profile updated for user %s', user.username)
        return user

class UserCoinsView(RetrieveAPIView):
    serializer_class = UserCoinsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AppUser.objects.only('id', 'coins')

    def get_object(self):
        return self.request.user


class AvatarListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvatarSerializer
    queryset = Avatar.objects.filter(state=True).order_by('name')


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    ALLOWED_CLIENT_IDS = [
        config('GOOGLE_WEB_CLIENT_ID', default=''),
        config('GOOGLE_ANDROID_CLIENT_ID', default=''),
        config('GOOGLE_IOS_CLIENT_ID', default=''),
    ]

    def _verify_token_audience(self, access_token):
        """Verify that the access token was issued for one of our client IDs"""
        token_info_url = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
        response = requests.get(token_info_url, params={'access_token': access_token})

        if response.status_code != status.HTTP_200_OK:
            logger.warning('Token info verification failed: %s', response.text)
            return False

        token_info = response.json()
        audience = token_info.get('aud', '')
        allowed = [cid for cid in self.ALLOWED_CLIENT_IDS if cid]

        if audience not in allowed:
            logger.warning(
                'Token audience mismatch. Got: %s, Expected one of: %s', audience, allowed
            )
            return False

        return True

    def post(self, request):
        access_token = request.data.get("accessToken")
        referral_code = request.data.get('referralCode')

        if not access_token:
            raise ValidationError({'access_token': 'Access token is required'})

        if not self._verify_token_audience(access_token):
            raise ValidationError({'access_token': 'Invalid or unauthorized token'})

        user_info_url = "https://www.googleapis.com/userinfo/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)

        if user_info_response.status_code != status.HTTP_200_OK:
            logger.error('Failed to fetch user info from Google: %s', user_info_response.text)
            raise ValidationError({'User': 'Failed to retrieve user info'})

        user_info = user_info_response.json()
        email = user_info.get("email")
        first_name = user_info.get("given_name", '')
        last_name = user_info.get("family_name", '')
        full_name = user_info.get("name")
        profile_pic = user_info.get('picture')

        user, created = AppUser.objects.get_or_create(
            email=email, 
            defaults={
                'username': generate_unique_field_value(AppUser, 'username', full_name), 
                'name': first_name, 
                'last_name': last_name,
            }
        )

        if created:
            logger.info('Creating new user %s', user.username)
            add_google_picture_app_user(user, profile_pic)
            if referral_code:
                referral_signup(user, referral_code)
        elif not user.profile_image:
            logger.info('Updating profile image for existing user %s', user.username)
            add_google_picture_app_user(user, profile_pic)
        else:
            logger.info('Existing user logged in: %s', user.username)

        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return Response(tokens)
    

def remove_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password) 
        if user:
            user.remove_user()
            return render(request, 'app_user/remove_user.html', {'message': 'User removed successfully'})
        else:
            return render(request, 'app_user/remove_user.html', {'message': 'Credentials are not correct'})

    return render(request, 'app_user/remove_user.html')


@csrf_exempt
def activate_user(request, uid, token):
    response = requests.post(f'{config("BACKEND_URL")}/api/users/activation/', data={
        'uid': uid,
        'token': token,
    })

    if response.status_code == 204:
        logger.info('User activated successfully: %s', uid)
        return render(request, 'email/activation_success.html')
    else:
        logger.error('Failed to activate user %s: %s', uid, response.text)
        return render(request, 'email/activation_error.html')


@csrf_exempt
def password_reset_confirm_view(request, uid, token):
    context = {
        'uid': uid, 
        'token': token, 
        'error': None, 
        'success': False
    }

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        re_new_password = request.POST.get('re_new_password')

        if not new_password or not re_new_password:
            context['error'] = 'Please fill in all fields.'
        elif new_password != re_new_password:
            context['error'] = 'Passwords do not match.'
        else:
            response = requests.post(
                f'{config("BACKEND_URL")}/api/users/reset_password_confirm/', 
                data={
                    'uid': uid,
                    'token': token,
                    'new_password': new_password,
                    're_new_password': re_new_password,
                }
            )

            if response.status_code == 204:
                logger.info('Password reset successfully for user: %s', uid)
                context['success'] = True
            else:
                logger.error('Password reset failed for user %s: %s', uid, response.text)
                context['error'] = response.json().get('detail', 'An error occurred.')

    return render(request, 'email/password_reset_form.html', context)