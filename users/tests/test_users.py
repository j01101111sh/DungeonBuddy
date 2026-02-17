import secrets

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

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
        with self.assertLogs("users.signals", level="INFO") as cm:
            _ = UserFactory.create(
                username="signal_test_user",
            )
            self.assertTrue(
                any("User created (signal): signal_test_user" in o for o in cm.output),
            )

    def test_signup_page_renders(self) -> None:
        """Test that the signup page renders correctly."""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/signup.html")
        self.assertContains(response, "Sign Up")

    def test_signup_successful(self) -> None:
        """Test that a user can sign up successfully."""
        url = reverse("signup")
        data = {
            "username": "new_signup_user",
            "email": "new@example.com",
            # Django's UserCreationForm requires two password fields
            "password1": "ComplexPass123!",
            "password2": "ComplexPass123!",
            "bio": "New adventurer",
            "location": "The Shire",
            "website": "http://shire.com",
        }
        response = self.client.post(url, data)

        # Should redirect to login page upon success
        self.assertRedirects(response, reverse("login"))

        # Verify user was created
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="new_signup_user").exists())

    def test_signup_sends_email(self) -> None:
        """Test that a confirmation email is sent upon successful signup."""
        url = reverse("signup")
        data = {
            "username": "email_user",
            "email": "email_user@example.com",
            "password1": "Pass123!",
            "password2": "Pass123!",
        }

        response = self.client.post(url, data)

        self.assertRedirects(response, reverse("login"))

        # Verify email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, "Welcome to Dungeon Buddy!")
        self.assertEqual(email.to, ["email_user@example.com"])
        self.assertIn("email_user", email.body)

    def test_signup_logs_masked_email(self) -> None:
        """Test that the signup log contains a masked email address."""
        url = reverse("signup")
        data = {
            "username": "logging_user",
            "email": "logging@example.com",
            "password1": "Pass123!",
            "password2": "Pass123!",
        }

        with self.assertLogs("users.views.signup", level="INFO") as cm:
            self.client.post(url, data)
            # logging -> l*****g
            self.assertTrue(
                any("l*****g@example.com" in o for o in cm.output),
                f"Logs found: {cm.output}",
            )

        # Test short email masking
        data["username"] = "short_email_user"
        data["email"] = "ab@example.com"
        with self.assertLogs("users.views.signup", level="INFO") as cm:
            self.client.post(url, data)
            # ab -> a*
            self.assertTrue(
                any("a*@example.com" in o for o in cm.output),
                f"Logs found: {cm.output}",
            )

        # Test single character email masking
        data["username"] = "one_char_email_user"
        data["email"] = "a@example.com"
        with self.assertLogs("users.views.signup", level="INFO") as cm:
            self.client.post(url, data)
            # a -> *
            self.assertTrue(
                any("*@example.com" in o for o in cm.output),
                f"Logs found: {cm.output}",
            )


class LoginViewTests(TestCase):
    def test_login_page_renders(self) -> None:
        """Test that the login page renders correctly."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertContains(response, "Log In")

    def test_login_successful(self) -> None:
        """Test that a user can log in with valid credentials."""
        # Create a user using the factory
        user, password = UserFactory.create(username="login_user")

        url = reverse("login")
        data = {
            "username": user.username,
            "password": password,
        }
        response = self.client.post(url, data)

        # Should redirect to LOGIN_REDIRECT_URL (default "/")
        self.assertRedirects(response, "/")

        # Check that the user is authenticated in the session
        self.assertTrue(int(self.client.session["_auth_user_id"]) == user.pk)

    def test_login_failure(self) -> None:
        """Test that login fails with invalid credentials."""
        user, _ = UserFactory.create(username="fail_user")

        url = reverse("login")
        data = {
            "username": user.username,
            "password": secrets.token_urlsafe(16),
        }
        response = self.client.post(url, data)

        # Should return 200 (re-render form) instead of redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

        # Ensure user is NOT logged in
        self.assertNotIn("_auth_user_id", self.client.session)
