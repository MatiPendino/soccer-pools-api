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


class TournamentListTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword',
            email='test@gmail.com', name='Test', last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser', password='testpassword',
            email='other@gmail.com', name='Other', last_name='User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.league = LeagueFactory()
        self.url = '/api/tournaments/tournament/'

    def test_list_requires_league_id(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_returns_paginated_results(self):
        for i in range(35):
            TournamentFactory(league=self.league, admin_tournament=self.other_user)
        response = self.client.get(f'{self.url}?league_id={self.league.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 30)
        self.assertIsNotNone(response.data['next'])

    def test_list_user_tournaments_first(self):
        # Create a tournament the user is a member of
        user_tournament = TournamentFactory(
            league=self.league, admin_tournament=self.user, name='AAA My Tournament'
        )
        TournamentUser.objects.create(
            tournament=user_tournament, user=self.user,
            tournament_user_state=TournamentUser.ACCEPTED
        )
        # Create another tournament with more participants
        popular = TournamentFactory(
            league=self.league, admin_tournament=self.other_user, name='ZZZ Popular'
        )
        for i in range(5):
            user = User.objects.create_user(
                username=f'pop{i}', password='test', email=f'pop{i}@test.com',
                name='Pop', last_name=str(i)
            )
            TournamentUser.objects.create(
                tournament=popular, user=user,
                tournament_user_state=TournamentUser.ACCEPTED
            )

        response = self.client.get(f'{self.url}?league_id={self.league.id}')
        results = response.data['results']
        self.assertEqual(results[0]['id'], user_tournament.id)

    def test_list_search_filters_by_name(self):
        TournamentFactory(league=self.league, admin_tournament=self.other_user, name='Alpha Cup')
        TournamentFactory(league=self.league, admin_tournament=self.other_user, name='Beta League')

        response = self.client.get(f'{self.url}?league_id={self.league.id}&search_text=Alpha')
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Alpha Cup')

    def test_list_includes_current_user_state(self):
        tournament = TournamentFactory(league=self.league, admin_tournament=self.other_user)
        TournamentUser.objects.create(
            tournament=tournament, user=self.user,
            tournament_user_state=TournamentUser.ACCEPTED
        )
        response = self.client.get(f'{self.url}?league_id={self.league.id}')
        results = response.data['results']
        self.assertEqual(results[0]['current_user_state'], TournamentUser.ACCEPTED)

    def test_list_current_user_state_null_when_not_member(self):
        TournamentFactory(league=self.league, admin_tournament=self.other_user)
        response = self.client.get(f'{self.url}?league_id={self.league.id}')
        results = response.data['results']
        self.assertIsNone(results[0]['current_user_state'])

    def test_list_includes_tournament_type(self):
        TournamentFactory(
            league=self.league, admin_tournament=self.other_user,
            tournament_type=Tournament.PRIVATE
        )
        response = self.client.get(f'{self.url}?league_id={self.league.id}')
        results = response.data['results']
        self.assertEqual(results[0]['tournament_type'], Tournament.PRIVATE)


class TournamentJoinTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword',
            email='test@gmail.com', name='Test', last_name='User'
        )
        self.admin = User.objects.create_user(
            username='admin', password='testpassword',
            email='admin@gmail.com', name='Admin', last_name='User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.league = LeagueFactory()

    def test_join_public_tournament_auto_accepts(self):
        tournament = TournamentFactory(
            league=self.league, admin_tournament=self.admin,
            tournament_type=Tournament.PUBLIC
        )
        response = self.client.post(f'/api/tournaments/tournament/{tournament.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tu = TournamentUser.objects.get(tournament=tournament, user=self.user)
        self.assertEqual(tu.tournament_user_state, TournamentUser.ACCEPTED)

    def test_join_private_tournament_creates_pending(self):
        tournament = TournamentFactory(
            league=self.league, admin_tournament=self.admin,
            tournament_type=Tournament.PRIVATE
        )
        response = self.client.post(f'/api/tournaments/tournament/{tournament.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tu = TournamentUser.objects.get(tournament=tournament, user=self.user)
        self.assertEqual(tu.tournament_user_state, TournamentUser.PENDING)

    def test_join_duplicate_returns_400(self):
        tournament = TournamentFactory(
            league=self.league, admin_tournament=self.admin,
            tournament_type=Tournament.PUBLIC
        )
        TournamentUser.objects.create(
            tournament=tournament, user=self.user,
            tournament_user_state=TournamentUser.ACCEPTED
        )
        response = self.client.post(f'/api/tournaments/tournament/{tournament.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_join_nonexistent_tournament_returns_404(self):
        response = self.client.post('/api/tournaments/tournament/99999/join/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
