from django.test import TestCase
from apps.app_user.factories import AppUserFactory
from apps.app_user.services import referral_signup
from apps.app_user.models import CoinGrant

class ReferralSignUpTest(TestCase):
    def setUp(self):
        self.referrer_user = AppUserFactory()
        self.referee_user = AppUserFactory()

    def test_referral_signup(self):
        coins_referrer = self.referrer_user.coins
        coins_referee = self.referee_user.coins
        referral_signup(self.referee_user, self.referrer_user.referral_code)
        
        self.referrer_user.refresh_from_db()
        self.referee_user.refresh_from_db()
        self.assertEqual(self.referee_user.referred_by, self.referrer_user)
        self.assertEqual(self.referrer_user.coins, coins_referrer + CoinGrant.REFERRAL_SIGNUP_AMOUNT)
        self.assertEqual(self.referee_user.coins, coins_referee + CoinGrant.REFERRAL_SIGNUP_AMOUNT)