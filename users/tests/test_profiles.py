from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import UserFactory

User = get_user_model()


class ProfileEditViewTests(TestCase):
    def setUp(self) -> None:
        self.user, self.password = UserFactory.create()
        self.url = reverse("profile_edit")

    def test_redirect_if_not_logged_in(self) -> None:
        """Test that unauthenticated users are redirected to the login page."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_page_renders_for_logged_in_user(self) -> None:
        """Test that the profile edit page renders correctly for authenticated users."""
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_edit.html")
        self.assertContains(response, "Bio")  # Check for form field label
        self.assertContains(response, self.user.bio)  # Check pre-filled data

    def test_update_profile_success(self) -> None:
        """Test that a user can successfully update their profile."""
        self.client.login(username=self.user.username, password=self.password)

        data = {
            "bio": "Updated bio content.",
            "location": "New Location, NY",
            "website": "https://updated-site.com",
        }
        response = self.client.post(self.url, data)

        # The view redirects back to the same page (success_url = reverse_lazy("profile_edit"))
        self.assertRedirects(response, self.url)

        # Reload user from DB to verify changes
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Updated bio content.")
        self.assertEqual(self.user.location, "New Location, NY")
        self.assertEqual(self.user.website, "https://updated-site.com")

        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Your profile has been updated successfully.",
        )

    def test_update_profile_invalid_url(self) -> None:
        """Test that invalid data (e.g. bad URL) prevents update and shows errors."""
        self.client.login(username=self.user.username, password=self.password)

        old_bio = self.user.bio
        data = {
            "bio": "This should not save",
            "location": "Nowhere",
            "website": "not-a-valid-url",  # Invalid URL format
        }
        response = self.client.post(self.url, data)

        # Should return 200 (re-render form) instead of redirect
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("website", form.errors)
        self.assertEqual(form.errors["website"], ["Enter a valid URL."])

        # Verify DB was NOT updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, old_bio)


class UserDetailViewTests(TestCase):
    def setUp(self) -> None:
        self.user, self.password = UserFactory.create(
            bio="A dedicated dungeon master.",
            location="Seattle, WA",
            website="https://dungeonmaster.com",
        )
        self.other_user, self.other_password = UserFactory.create()
        self.url = reverse("user_detail", kwargs={"username": self.user.username})

    def test_redirect_if_not_logged_in(self) -> None:
        """Test that unauthenticated users are redirected to the login page."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_page_renders_with_profile_info(self) -> None:
        """Test that the user detail page renders with the correct profile information."""
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/user_detail.html")
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.bio)
        self.assertContains(response, self.user.location)
        self.assertContains(response, self.user.website)

    def test_edit_button_visible_for_owner(self) -> None:
        """Test that the 'Edit Profile' button is visible when the user views their own profile."""
        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.url)
        self.assertContains(response, "Edit Profile")
        self.assertContains(response, reverse("profile_edit"))

    def test_edit_button_hidden_for_others(self) -> None:
        """Test that the 'Edit Profile' button is NOT visible when viewing another user's profile."""
        # Login as a different user
        self.client.login(
            username=self.other_user.username,
            password=self.other_password,
        )
        response = self.client.get(self.url)
        edit_url = reverse("profile_edit")
        self.assertNotContains(response, f'href="{edit_url}" role="button">')

    def test_profile_without_bio(self) -> None:
        """Test that the profile page renders correctly for a user without a bio."""
        user_no_bio, password = UserFactory.create(bio="")
        self.client.login(username=user_no_bio.username, password=password)
        url = reverse("user_detail", kwargs={"username": user_no_bio.username})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, user_no_bio.username)
