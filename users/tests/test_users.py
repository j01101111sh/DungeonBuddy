import secrets

from django.contrib.auth import get_user_model
from django.test import TestCase

from config.tests.factories import UserFactory


class CustomUserModelTests(TestCase):
    def test_create_user(self) -> None:
        """Test that a user can be created with a username and password."""
        user, _ = UserFactory.create(
            username="testuser",
        )
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self) -> None:
        """Test that a superuser can be created."""
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="adminuser",
            password=secrets.token_urlsafe(16),
            email=None,
        )
        self.assertEqual(admin_user.username, "adminuser")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_profile_fields(self) -> None:
        """Test that custom profile fields can be saved."""
        user, _ = UserFactory.create(
            bio="I love mystery movies.",
            location="Baker Street",
            website="https://example.com",
        )
        self.assertEqual(user.bio, "I love mystery movies.")
        self.assertEqual(user.location, "Baker Street")
        self.assertEqual(user.website, "https://example.com")

    def test_test_user_flag(self) -> None:
        """Test the is_test_user flag."""
        # Test default is False
        user_normal, _ = UserFactory.create()
        self.assertFalse(user_normal.is_test_user)

        # Test setting to True
        user_test, _ = UserFactory.create(
            is_test_user=True,
        )
        self.assertTrue(user_test.is_test_user)

    def test_string_representation(self) -> None:
        """Test the model's string representation uses the username."""
        user, _ = UserFactory.create(
            username="testuser2",
        )
        self.assertEqual(str(user), "testuser2")


class SignUpViewTests(TestCase):
    def test_user_creation_logging(self) -> None:
        """Test that user creation triggers a log message via signals."""
        # assertLogs captures logs from the 'users.signals' logger
        with self.assertLogs("users.signals", level="INFO") as cm:
            _ = UserFactory.create(
                username="signal_test_user",
            )

            # Verify the log message was captured
            self.assertTrue(
                any("User created (signal): signal_test_user" in o for o in cm.output),
            )
