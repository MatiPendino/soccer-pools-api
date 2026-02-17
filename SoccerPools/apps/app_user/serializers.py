from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from PIL import Image
from django.contrib.auth import get_user_model
from .models import CoinGrant, Avatar
from .validations import username_validator
from .services import referral_signup

User = get_user_model()

class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = ('id', 'image')


class UserEditableSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        validators=[
            username_validator,
            UniqueValidator(queryset=User.objects.all(), message='Username is taken')
        ]
    )
    profile_image = serializers.ImageField(required=False, allow_null=True)
    avatar_id = serializers.PrimaryKeyRelatedField(
        queryset=Avatar.objects.filter(state=True), 
        write_only=True, required=False, allow_null=True,
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'name', 'last_name', 'profile_image', 'instagram_username', 
            'twitter_username', 'avatar_id',
        )

    def validate_username(self, value):
        if not value:
            return value

        # Validate there is no existing user with that username
        users = User.objects.filter(username__iexact=value)
        if self.instance:
            users = users.exclude(pk=self.instance.pk)
        if users.exists():
            raise serializers.ValidationError('Username is taken')

        return value
    
    def validate_profile_image(self, image):
        if image is None:
            return image

        # 5MB Size limit
        if image.size > 5*1024*1024:
            raise serializers.ValidationError('Max image size is 5MB')

        # Real image
        try:
            img = Image.open(image)
            img.verify()
        except Exception:
            raise serializers.ValidationError('Invalid image file')
        
        return image

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar_id', None)
        if avatar:
            instance.profile_image = avatar.image
            instance.save(update_fields=['profile_image'])
        return super().update(instance, validated_data)


class UserRegisterSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'last_name', 'password', 'referral_code')

    def create(self, clean_data):
        user_obj = User.objects.create_user(
            email=clean_data['email'], 
            password=clean_data['password'],
            username=clean_data['username'],
            name=clean_data['name'],
            last_name=clean_data['last_name']
        )

        try:
            referral_code = clean_data.get('referral_code')
            if referral_code:
                referral_signup(user_obj, referral_code)
        except User.DoesNotExist:
            pass

        # User will be inactive until registration confirmed via email
        user_obj.is_active = False
        user_obj.save(update_fields=['is_active'])
        return user_obj
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'name', 'last_name', 'profile_image', 'coins',
            'referral_code',
        )


class UserCoinsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['coins']


class UserMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'profile_image', 'created_at')
        

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