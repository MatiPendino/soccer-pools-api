import string, secrets

def generate_referral_code(n=12):
    """Generate a random alphanumeric referral code of length n"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))
