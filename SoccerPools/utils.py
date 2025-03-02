from decouple import config

def get_settings_env():
    PRODUCTION_ENV_PATH = 'SoccerPools.settings.production'
    LOCAL_ENV_PATH = 'SoccerPools.settings.local'
    is_production_env = bool(int(config('IS_PRODUCTION_ENV')))

    settings_env = PRODUCTION_ENV_PATH if is_production_env else LOCAL_ENV_PATH
    return settings_env