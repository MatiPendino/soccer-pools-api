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
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, NotFound
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.shortcuts import render
from utils import generate_unique_field_value
from apps.bet.models import BetLeague
from apps.league.serializers import LeagueSerializer
from .models import AppUser, CoinGrant
from .serializers import UserSerializer, AddCoinsSerializer, UserEditableSerializer
from .services import grant_coins

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


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("accessToken")
        if not access_token:
            raise ValidationError({'access_token': 'Access token is required'})

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

        if created or not user.profile_image:
            logger.info('Creating new user or updating profile image for user %s', user.id)
            response = requests.get(profile_pic)
            if response.status_code == status.HTTP_200_OK:
                image_file = ContentFile(response.content)
                user.profile_image.save(f"{user.username}_profile.jpg", image_file)
                user.save()
        else:
            logger.info('Existing user logged in: %s', user.id)

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