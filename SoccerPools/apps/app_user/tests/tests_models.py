from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.app_user.models import AppUser

class AppUserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        AppUser.objects.create_user(
            email='testing@gmail.com',
            name='Mati',
            last_name='Pendino',
            username='matipendino',
            password='123456789',
            balance=1
        )

    def test_negative_balance(self):
        app_user = AppUser.objects.get(id=1)
        app_user.balance = -1
        with self.assertRaises(ValidationError):
            app_user.clean_fields()

    def test_username_no_spaces(self):
        app_user = AppUser.objects.get(id=1)
        app_user.username = 'Matias Pendino'
        with self.assertRaises(ValidationError):
            app_user.full_clean()

    def test_profile_image_upload(self):
        profile_image_content = b'file_content'
        profile_image = SimpleUploadedFile('test_image.jpg', profile_image_content, content_type='image/jpeg')
        instance = AppUser.objects.create_user(
            email='testing2@gmail.com',
            name='Mati',
            last_name='Pendino',
            username='matipendino2',
            password='123456789',
            balance=1,
            profile_image=profile_image
        )
        saved_instance = AppUser.objects.get(id=instance.id)

        self.assertEqual(saved_instance.profile_image.read(), profile_image_content)

    