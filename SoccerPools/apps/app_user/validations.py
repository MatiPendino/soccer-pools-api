from django.core.exceptions import ValidationError

def validate_no_spaces(value):
    if ' ' in value:
        raise ValidationError('Username cannot contain spaces.')

