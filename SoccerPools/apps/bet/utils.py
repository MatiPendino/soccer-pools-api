import string
import random

def generate_unique_code(model):
    characters = string.ascii_letters + string.digits
    while True:
        unique_code = ''.join(random.choices(characters, k=13))
        if not model.objects.filter(operation_code=unique_code).exists():
            return unique_code