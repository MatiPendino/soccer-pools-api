from decouple import config

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