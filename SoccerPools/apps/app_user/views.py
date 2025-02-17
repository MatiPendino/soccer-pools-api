import requests
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.bet.models import BetRound
from apps.league.models import League
from apps.match.models import MatchResult
from apps.league.serializers import LeagueSerializer
from .models import AppUser
from .serializers import UserLoginSerializer, UserRegisterSerializer, UserSerializer


class UserRegister(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.create(request.data)
            if user:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
            

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
    

class UserView(APIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        response = Response({'user': serializer.data}, status=status.HTTP_200_OK)
        return response
    

class UserDestroyApiView(APIView):
    """
        The User, and all their bets and match results will be logically removed
    """
    def delete(self, request, *args, **kwargs):
        user = request.user
        if user:
            user.remove_user()
            return Response({'success': 'User removed successfully'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)


class UserInLeague(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        """
            If the user is in at least one league returns True, otherwise False

            in_league: Bool
        """
        if BetRound.objects.filter(user=request.user, state=True).exists():
            return Response({'in_league': True})
        
        return Response({'in_league': False})
    

class LeagueUser(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
            Gets the League based on the User

            TODO update once multileague feature created
        """
        try:
            bet_round = BetRound.objects.filter(user=request.user, state=True).first()
            league = League.objects.filter(round__bet_rounds=bet_round, state=True).distinct().first()
            league_serializer = LeagueSerializer(league)

            return Response(league_serializer.data)
        except Exception as err:
            return Response({'error': str(err)}, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("accessToken")
        if not access_token:
            return Response({"error": "Access token is required"}, status=status.HTTP_400_BAD_REQUEST)

        user_info_url = "https://www.googleapis.com/userinfo/v2/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers)

        if user_info_response.status_code != status.HTTP_200_OK:
            return Response({"error": "Failed to retrieve user info"}, status=user_info_response.status_code)

        user_info = user_info_response.json()
        email = user_info.get("email")
        first_name = user_info.get("given_name", '')
        last_name = user_info.get("family_name", '')
        full_name = user_info.get("name")
        profile_pic = user_info.get('picture')

        user, created = AppUser.objects.get_or_create(
            email=email, 
            defaults={
                'username': slugify(full_name), 
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