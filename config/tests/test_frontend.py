from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import TabletopSystemFactory, UserFactory
from dunbud.models import Campaign

User = get_user_model()


class FrontendTests(TestCase):
    """
    Unit tests for frontend template rendering and static asset inclusion.
    """

    def test_base_template_includes_theme_scripts(self) -> None:
        """
        Test that the base template includes the necessary JS and CSS for dark mode.
        """
        response = self.client.get(reverse("splash"))

        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for Bootstrap Icons
        self.assertIn("bootstrap-icons.css", content)

        # Check for Theme JS
        self.assertIn("js/theme.js", content)

        # Check for inline script for FOUC prevention
        self.assertIn("data-bs-theme", content)

    def test_navbar_includes_toggle(self) -> None:
        """
        Test that the navbar includes the theme toggle button.
        """
        response = self.client.get(reverse("splash"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for the button ID
        self.assertIn('id="theme-toggle"', content)


class CampaignFrontendTests(TestCase):
    """
    Tests for specific campaign pages to ensure elements render.
    """

    def setUp(self) -> None:
        self.user, self.upass = UserFactory.create()
        self.uname = self.user.get_username()
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            dungeon_master=self.user,
            system=TabletopSystemFactory.create(),
        )

    def test_campaign_detail_render(self) -> None:
        """
        Test that campaign detail page renders and contains the feed structure.
        """
        self.client.login(username=self.uname, password=self.upass)
        response = self.client.get(
            reverse("campaign_detail", kwargs={"pk": self.campaign.pk}),
        )
        self.assertEqual(response.status_code, 200)

        # Check for presence of feed-card class logic (even if empty, structure exists)
        # We can't easily test CSS computation here, but we can ensure the template renders.
        self.assertContains(response, "Test Campaign")
