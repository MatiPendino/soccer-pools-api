import requests
from decouple import config
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import F
from utils import generate_unique_field_value
from apps.bet.models import BetLeague
from apps.league.serializers import LeagueSerializer
from .models import AppUser
from .serializers import UserLoginSerializer, UserRegisterSerializer, UserSerializer


class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.create(request.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            

class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        data = request.data
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.check_user(data)
            login(request, user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        

class UserLogout(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)
    

class LegacyUserApiView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        response = Response(serializer.data, status=status.HTTP_200_OK)
        return response
    
        
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
        coins = request.data.get('coins')
        if coins is None:
            raise ValidationError({'coins': 'Coins were not provided'})

        user = request.user
        user.coins = F('coins') + int(coins)
        user.save()
        user.refresh_from_db()
        return Response({'coins': user.coins}, status=status.HTTP_200_OK)
    

class UserDestroyApiView(APIView):
    """
        The User, and all their bets and match results will be logically removed
    """
    def delete(self, request, *args, **kwargs):
        user = request.user
        if user:
            user.remove_user()
            return Response({'success': 'User removed successfully'}, status=status.HTTP_204_NO_CONTENT)
        raise AppUser.DoesNotExist 


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


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("accessToken")
        if not access_token:
            raise ValidationError('Access token is required')

        user_info_url = "https://www.googleapis.com/userinfo/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)

        if user_info_response.status_code != status.HTTP_200_OK:
            raise ValidationError('Failed to retrieve user info')

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
            response = requests.get(profile_pic)
            if response.status_code == status.HTTP_200_OK:
                image_file = ContentFile(response.content)
                user.profile_image.save(f"{user.username}_profile.jpg", image_file)
                user.save()

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
        return render(request, 'email/activation_success.html')
    else:
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
                context['success'] = True
            else:
                print()
                context['error'] = response.json().get('detail', 'An error occurred.')

    return render(request, 'email/password_reset_form.html', context)