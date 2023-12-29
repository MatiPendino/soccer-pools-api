from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

class UserRegisterViewTest(TestCase):
    def setUp(self):
        self.register_url = reverse('user_register')
        self.client = APIClient()

    def test_user_registration_success(self):
        data = {
            'username': 'mati',
            'email': 'mati@gmail.com',
            'name': 'Matias',
            'last_name': 'Pendino',
            'password': '123456789'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_registration_failure(self):
        data = {'username': 'fail'}
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        get_user_model().objects.create_user(
            username='mati',
            email='mati@gmail.com',
            name='Matias',
            last_name='Pendino',
            password='123456789'
        )

    def setUp(self):
        self.login_url = reverse('user_login')
        self.client = APIClient()

    def test_user_login_success(self):
        data = {
            'username': 'mati',
            'password': '123456789'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_login_failure(self):
        data = {
            'username': 'mati',
            'password': '12345678'
        }
        with self.assertRaises(ValueError):
            self.client.post(self.login_url, data, format='json')

    def test_missing_login_data(self):
        data_no_password = {'username': 'mati'}
        response = self.client.post(self.login_url, data_no_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data_no_username = {'password': '123456789'}
        response = self.client.post(self.login_url, data_no_username, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLogoutViewTest(TestCase):
    def setUp(self):
        self.logout_url = reverse('user_logout')
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='mati',
            email='email@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )

    def test_logout_no_authenticated_user(self):
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserViewTest(TestCase):
    def setUp(self):
        self.view_url = reverse('user_view')
        self.client = APIClient()

    def test_view_user_logged(self):
        user = get_user_model().objects.create_user(
            username='mati',
            email='email@gmail.com',
            name='Mati',
            last_name='Pendino',
            password='123456798'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_user_not_logged(self):
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)



