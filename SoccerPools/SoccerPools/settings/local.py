from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

INTERNAL_IPS = [
    '127.0.0.1',
    '172.20.10.8',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'db',
        'PORT': config('DB_PORT', '5432')
    }
}

# Run Celery tasks immediately (eager mode)
CELERY_TASK_ALWAYS_EAGER = True

# Propagate errors to Django when tasks fail
CELERY_TASK_EAGER_PROPAGATES = True

# Allow all hosts for CORS
CORS_ALLOW_ALL_ORIGINS = True

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
