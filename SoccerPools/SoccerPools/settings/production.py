from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from django.core.exceptions import DisallowedHost

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS').split(',')
CORS_PREFLIGHT_MAX_AGE = 3600

INTERNAL_IPS = [
    '127.0.0.1',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'db',
        'PORT': config('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Production security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'same-origin'

# AWS Settings
_AWS_EXPIRY = 86400  # 1 day
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate",
}

def before_send(event, hint):
    # Check if this event was triggered by an exception
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # If the exception is DisallowedHost (invalid Host header), ignore this event
        if isinstance(exc_value, DisallowedHost):
            return None

    return event 

# Sentry settings
sentry_sdk.init(
    dsn=f'https://{config("SENTRY_URL")}.ingest.us.sentry.io/{config("SENTRY_KEY")}',
    traces_sample_rate=0.1,
    integrations=[DjangoIntegration(), CeleryIntegration()],
    profiles_sample_rate=0.1,
    send_default_pii=True,
    environment='production',
    before_send=before_send,
)