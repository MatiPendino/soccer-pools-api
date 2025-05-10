from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.app_user.serializers import UserRegisterSerializer, UserLoginSerializer
from apps.app_user.models import AppUser

class UserRegisterSerializerTest(TestCase):
    
    def test_no_profile_image(self):
        data = {
            'username': 'matipendino',
            'email': 'mati@gmail.com',
            'name': 'Mati',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_no_password(self):
        data = {
            'username': 'matipendino',
            'email': 'mati@gmail.com',
            'name': 'Mati',
            'last_name': 'Pendino',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_no_email(self):
        data = {
            'username': 'matipendino',
            'name': 'Mati',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_no_username(self):
        data = {
            'email': 'mati@gmail.com',
            'name': 'Mati',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_no_name(self):
        data = {
            'username': 'matipendino',
            'email': 'mati@gmail.com',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_no_last_name(self):
        data = {
            'username': 'matipendino',
            'email': 'mati@gmail.com',
            'name': 'Mati',
            'password': '123456789'
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class UserLoginSerializerTest(TestCase):

    def test_existing_user(self):
        data = {
            'username': 'existing',
            'email': 'exist@gmail.com',
            'name': 'Existing',
            'last_name': 'A', 
            'password': '123456789'
        }
        app_user = AppUser.objects.create_user(**data)
        serializer = UserLoginSerializer(
            data={'username': data.get('username'), 'password': data.get('password')}
        )
        if serializer.is_valid():
            self.assertEqual(app_user, serializer.check_user({'username': data.get('username'), 'password': data.get('password')}))
        

    def test_not_existing_user(self):
        data = {'username': 'not_existing', 'password': '123456789'}
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            with self.assertRaises(ValidationError):
                serializer.check_user(data)