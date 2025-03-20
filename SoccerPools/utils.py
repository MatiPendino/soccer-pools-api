import string
import random
from decouple import config
from django.utils.text import slugify

def get_settings_env():
    PRODUCTION_ENV_PATH = 'SoccerPools.settings.production'
    LOCAL_ENV_PATH = 'SoccerPools.settings.local'
    is_production_env = bool(int(config('IS_PRODUCTION_ENV')))

    settings_env = PRODUCTION_ENV_PATH if is_production_env else LOCAL_ENV_PATH
    return settings_env


def custom_exception_handler(exc, context):
    """
    Custom exception handler that ensures error responses have a consistent format.
    """
    # Causes an Improperly configured error when imported globally
    from rest_framework.views import exception_handler 
    response = exception_handler(exc, context)

    if response is not None:
        details = response.data.get('detail', None)
        response.data = {
            'errors': response.data,
            'status_code': response.status_code,
            'error_type': exc.__class__.__name__
        }
        if details:
            response.data['details'] = details

    return response


def generate_unique_field_value(model, field_name, value):
    """
    Generates a unique value for a given model and field.

    Parameters:
    - model: The Django model to check uniqueness against.
    - field_name: The field to check for uniqueness.
    - value: The initial value to be slugified and checked.
    - max_length: The maximum allowed length for the field.

    Returns:
    - A unique field value (e.g., username, slug, etc.).
    """
    base_value = slugify(value) 
    unique_value = base_value
    characters = string.ascii_letters + string.digits
    unique_code_length = 6

    # Check if the field value already exists in the model
    while model.objects.filter(**{field_name: unique_value}).exists():
        unique_code = ''.join(random.choices(characters, k=unique_code_length))
        unique_value = f"{base_value}-{unique_code}"

    return unique_value