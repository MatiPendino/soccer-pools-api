from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import CoinGrant

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'last_name', 'password')

    def create(self, clean_data):
        user_obj = User.objects.create_user(
            email=clean_data['email'], 
            password=clean_data['password'],
            username=clean_data['username'],
            name=clean_data['name'],
            last_name=clean_data['last_name']
        )
        # User will be inactive until registration confirmed via email
        user_obj.is_active = False
        user_obj.save()
        return user_obj
    

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def check_user(self, clean_data):
        user = authenticate(username=clean_data.get('username'), password=clean_data.get('password'))
        if not user:
            raise ValidationError('User not found.')
        return user
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name', 'last_name', 'profile_image', 'coins')


class AddCoinsSerializer(serializers.Serializer):
    reward_type = serializers.ChoiceField(
        choices=[CoinGrant.AD_REWARD, CoinGrant.APP_REVIEW], 
        default=CoinGrant.AD_REWARD
    )
    coins = serializers.IntegerField()

    def validate(self, data):
        reward_type = data.get('reward_type')
        coins = data.get('coins')

        if reward_type not in [CoinGrant.AD_REWARD, CoinGrant.APP_REVIEW]:
            raise serializers.ValidationError({'type': 'Invalid reward type'})
        
        if coins != CoinGrant.AD_REWARD_AMOUNT and coins != CoinGrant.APP_REVIEW_AMOUNT:
            raise serializers.ValidationError({'coins': 'Invalid amount of coins'})
        
        return data