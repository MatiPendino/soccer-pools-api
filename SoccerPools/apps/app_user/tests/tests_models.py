from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

User = get_user_model()

class AppUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(
            email='testin@gmail.com',
            name='Mati',
            last_name='Pendino',
            username='matipendino',
            password='123456789',
            balance=1
        )

    def test_negative_balance(self):
        user = User.objects.all().first()
        user.balance = -1
        with self.assertRaises(ValidationError):
            user.clean_fields()

    def test_negative_coins(self):
        user = User.objects.all().first()
        user.coins = -1
        with self.assertRaises(ValidationError):
            user.clean_fields()

    def test_username_no_spaces(self):
        user = User.objects.all().first()
        user.username = 'Matias Pendino'
        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_profile_image_upload(self):
        profile_image_content = b'file_content'
        profile_image = SimpleUploadedFile('test_image.jpg', profile_image_content, content_type='image/jpeg')
        instance = User.objects.create_user(
            email='testing2@gmail.com',
            name='Mati',
            last_name='Pendino',
            username='matipendino2',
            password='123456789',
            balance=1,
            profile_image=profile_image
        )
        saved_instance = User.objects.get(id=instance.id)

        self.assertEqual(saved_instance.profile_image.read(), profile_image_content)

    