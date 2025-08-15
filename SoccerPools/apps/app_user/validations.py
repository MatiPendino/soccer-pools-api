from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

def validate_no_spaces(value):
    if ' ' in value:
        raise ValidationError('Username cannot contain spaces.')


USERNAME_REGEX = r'^[a-zA-Z0-9._-]{3,30}$'
username_validator = RegexValidator(
    USERNAME_REGEX,
    'Username must be 3–30 chars: letters, numbers, dot, underscore, hyphen.'
)
