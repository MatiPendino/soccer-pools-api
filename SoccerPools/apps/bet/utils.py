import string
import random
from apps.bet.models import BetRound

def generate_unique_code():
    characters = string.ascii_letters + string.digits
    unique_code = ''.join(random.choices(characters, k=13))    
    try:
        operation_code = BetRound.objects.get(operation_code=unique_code)
        return generate_unique_code()
    except:
        return unique_code