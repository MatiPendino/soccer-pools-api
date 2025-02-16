from decouple import config
import requests
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Tournament

def generate_default_logo():
    RELATIVE_DEFAULT_LOGO_URL = f'{Tournament.LOGO_FOLDER_NAME}/{Tournament.LOGO_DEFAULT_FILE_NAME}'
    ABSOLUTE_DEFAULT_LOGO_URL = f'{config("AWS_S3_BUCKET_URL")}/{RELATIVE_DEFAULT_LOGO_URL}'

    response = requests.get(ABSOLUTE_DEFAULT_LOGO_URL)
    if response.status_code == 200:
        image_data = response.content
        image_file = BytesIO(image_data)
        file = InMemoryUploadedFile(image_file, None, RELATIVE_DEFAULT_LOGO_URL, 'image/png', len(image_data), None)
        return file
    else:
        raise Exception