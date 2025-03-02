"""
WSGI config for SoccerPools project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from utils import get_settings_env

from django.core.wsgi import get_wsgi_application

settings_env = get_settings_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_env)

application = get_wsgi_application()
