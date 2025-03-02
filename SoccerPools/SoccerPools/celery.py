import os
from celery import Celery
from utils import get_settings_env

settings_env = get_settings_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_env)

app = Celery('SoccerPools')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
