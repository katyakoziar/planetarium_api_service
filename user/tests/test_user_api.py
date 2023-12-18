from django.test import TestCase
from django.contrib.auth import get_user_model


class UserManagerTests(TestCase):
    def test_create_user(self):
        user = get_user_model().objects.create_user(
            email="simple@user.com",
            password="password"
        )
        self.assertEqual(user.email, "simple@user.com")
        self.assertTrue(user.check_password("password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = get_user_model().objects.create_superuser(
            "super@user.com",
            "password"
        )
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.check_password("password"))
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_user_without_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="password")
