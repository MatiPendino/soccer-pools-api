from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'last_name', 'birthdate', 'profile_image', 'password')

    def create(self, clean_data):
        user_obj = User.objects.create_user(
            email=clean_data['email'], 
            password=clean_data['password'],
            username=clean_data['username'],
            birthdate=clean_data['birthdate'],
            name=clean_data['name'],
            last_name=clean_data['last_name']
        )
        if clean_data.get('profile_image'):
            user_obj.profile_image = clean_data['profile_image']
        user_obj.save()
        return user_obj
    

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def check_user(self, clean_data):
        user = authenticate(username=clean_data.get('username'), password=clean_data.get('password'))
        if not user:
            raise ValueError('User not found.')
        return user
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'last_name', 'profile_image')