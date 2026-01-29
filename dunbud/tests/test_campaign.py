import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import UserFactory
from dunbud.models import Campaign

User = get_user_model()


class CampaignModelTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_user")
        self.player, _ = UserFactory.create(username="player_user")

    def test_create_campaign(self) -> None:
        """
        Test that a Campaign can be created with required fields.
        """
        campaign = Campaign.objects.create(
            name="The Heroes",
            dungeon_master=self.dm,
            description="A legendary group.",
        )
        self.assertEqual(campaign.name, "The Heroes")
        self.assertEqual(campaign.dungeon_master, self.dm)
        self.assertEqual(campaign.description, "A legendary group.")
        # Verify the ID is a UUID
        self.assertIsInstance(campaign.pk, uuid.UUID)

    def test_add_players(self) -> None:
        """
        Test that players can be added to a campaign.
        """
        campaign = Campaign.objects.create(
            name="Dungeon Crawlers",
            dungeon_master=self.dm,
        )
        campaign.players.add(self.player)
        self.assertIn(self.player, campaign.players.all())

    def test_string_representation(self) -> None:
        """
        Test the string representation of the Campaign model.
        """
        campaign = Campaign.objects.create(
            name="Vox Machina",
            dungeon_master=self.dm,
        )
        self.assertEqual(str(campaign), "Vox Machina")

    def test_campaign_creation_logs(self) -> None:
        """
        Test that creating a campaign triggers a log message.
        """
        with self.assertLogs("dunbud.models", level="INFO") as cm:
            Campaign.objects.create(
                name="Logged Campaign",
                dungeon_master=self.dm,
            )
            self.assertTrue(
                any("New campaign created: Logged Campaign" in m for m in cm.output),
            )


class CampaignCreateViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="testuser")
        self.url = reverse("campaign_create")

    def test_create_campaign_view_access_anonymous(self) -> None:
        """
        Test that anonymous users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_create_campaign_view_access_authenticated(self) -> None:
        """
        Test that authenticated users can access the create page.
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/campaign_form.html")

    def test_create_campaign_success(self) -> None:
        """
        Test that a campaign is created successfully and DM is set.
        """
        self.client.force_login(self.user)
        data = {
            "name": "New Adventure",
            "description": "A grand journey.",
        }
        response = self.client.post(self.url, data)

        # Check redirection to success_url (splash)
        self.assertRedirects(response, reverse("splash"))

        # Check database
        campaign = Campaign.objects.get(name="New Adventure")
        self.assertEqual(campaign.dungeon_master, self.user)
        self.assertEqual(campaign.description, "A grand journey.")
        self.assertIsInstance(campaign.pk, uuid.UUID)

    def test_create_campaign_view_logs(self) -> None:
        """
        Test that the view logs the creation event.
        """
        self.client.force_login(self.user)
        data = {"name": "View Logged Campaign", "description": "Test"}

        with self.assertLogs("dunbud.views", level="INFO") as cm:
            self.client.post(self.url, data)
            self.assertTrue(
                any(
                    "Campaign created via view: View Logged Campaign" in m
                    for m in cm.output
                ),
            )
