from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_email_is_normalized_and_used_as_login(self):
        user = get_user_model().objects.create_user("ColdChain@EXAMPLE.com", "safe-password")

        self.assertEqual(user.email, "coldchain@example.com")
        self.assertEqual(user.USERNAME_FIELD, "email")
        self.assertTrue(user.check_password("safe-password"))
        self.assertEqual(user.role, get_user_model().Role.OPERATOR_1)

    def test_superuser_is_admin_role(self):
        user = get_user_model().objects.create_superuser("admin@example.com", "safe-password")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, get_user_model().Role.ADMIN)
