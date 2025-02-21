import string
import random

def generate_unique_code(model):
    characters = string.ascii_letters + string.digits
    while True:
        unique_code = ''.join(random.choices(characters, k=13))
        if not model.objects.filter(operation_code=unique_code).exists():
            return unique_code
        

def generate_response_data(league_name, username, bet_league_id, bet_rounds):
        return {
            'league': league_name,
            'user': username,
            'bet_league_id': bet_league_id,
            'bet_rounds': [
                {'bet_round_id': bet_round.id, 'round_id': bet_round.round.id} 
                for bet_round in bet_rounds
            ]
        }