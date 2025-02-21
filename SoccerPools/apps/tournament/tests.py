import io
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.league.factories import LeagueFactory
from .factories import TournamentFactory
from apps.tournament.models import Tournament, TournamentUser

User = get_user_model()
class TournamentViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpassword',
            email='test@gmail.com',
            name='TestName',
            last_name='TestSurname'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.league = LeagueFactory()
        self.tournament = TournamentFactory(league=self.league, admin_tournament=self.user)
        self.url = '/api/tournaments/tournament/'

    def test_tournament_creation(self):
        # Create a valid image file in memory to test logo upload
        image = Image.new('RGB', (100, 100)) 
        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.seek(0)

        logo = SimpleUploadedFile(
            name='test_logo.jpg', 
            content=image_file.read(),
            content_type='image/jpeg'
        )

        tournament_data = {
            'name': 'Example Tournament',
            'description': 'Example tournament for testing',
            'logo': logo,
            'league': self.league.id,
            'admin_tournament': self.user.id,
        }
        response = self.client.post(self.url, tournament_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Tournament.objects.count(), 2)
        self.assertEqual(TournamentUser.objects.count(), 1)
        self.assertEqual(TournamentUser.objects.count(), Tournament.objects.last().n_participants)

    def test_tournament_creation_invalid_image(self):
        logo = SimpleUploadedFile(
            name='test_logo.jpg', 
            content=b'this-image-doesnt-exist',
            content_type='image/jpeg'
        )
        tournament_data = {
            'name': 'Example Invalid Tournament',
            'logo': logo,
            'league': self.league.id,
            'admin_tournament': self.user.id,
        }

        response = self.client.post(self.url, tournament_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
