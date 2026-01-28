import secrets

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from config.tests.factories import UserFactory
from users.forms import CustomUserCreationForm


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
    def test_signup_page_status_code(self) -> None:
        """Test that the signup page returns a 200 status code."""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

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

    def test_signup_page_template(self) -> None:
        """Test that the correct template is used for the signup page."""
        response = self.client.get(reverse("signup"))
        self.assertTemplateUsed(response, "registration/signup.html")

    def test_signup_form(self) -> None:
        """Test that the signup form is the CustomUserCreationForm."""
        response = self.client.get(reverse("signup"))
        self.assertIsInstance(response.context["form"], CustomUserCreationForm)

    def test_signup(self) -> None:
        """Test that a user can be created by posting to the signup page."""
        User = get_user_model()
        upass = secrets.token_urlsafe(16)
        self.assertEqual(User.objects.count(), 0)
        response = self.client.post(
            reverse("signup"),
            {"username": "newuser", "password1": upass, "password2": upass},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        self.assertRedirects(response, reverse("login"))

    def test_signup_csrf_error(self) -> None:
        """Test that the signup page enforces CSRF protection."""
        # Create a client that enforces CSRF checks
        csrf_client = Client(enforce_csrf_checks=True)
        upass = secrets.token_urlsafe(16)

        response = csrf_client.post(
            reverse("signup"),
            {"username": "csrf_test_user", "password1": upass, "password2": upass},
        )

        # Expect a 403 Forbidden response due to missing CSRF token
        self.assertEqual(response.status_code, 403)
