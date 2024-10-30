from django.contrib.auth.tokens import PasswordResetTokenGenerator
from home.models import UserProfile
import six


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        user2 = UserProfile.objects.get(user=user)
        return six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user2.email_confirmed)


account_activation_token = AccountActivationTokenGenerator()