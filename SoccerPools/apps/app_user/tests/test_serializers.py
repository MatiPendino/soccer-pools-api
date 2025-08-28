from django.test import TestCase
from apps.app_user.serializers import UserRegisterSerializer

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
