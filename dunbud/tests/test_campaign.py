import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import UserFactory
from dunbud.models import Campaign, TabletopSystem

User = get_user_model()


class CampaignModelTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_user")
        self.player, _ = UserFactory.create(username="player_user")
        self.system = TabletopSystem.objects.create(
            name="D&D 5e",
            description="Fifth edition of Dungeons & Dragons",
        )

    def test_create_campaign(self) -> None:
        """
        Test that a Campaign can be created with required fields and links.
        """
        campaign = Campaign.objects.create(
            name="The Heroes",
            dungeon_master=self.dm,
            description="A legendary group.",
            system=self.system,
            vtt_link="https://foundryvtt.com/game",
            video_link="https://zoom.us/j/123456",
        )
        self.assertEqual(campaign.name, "The Heroes")
        self.assertEqual(campaign.dungeon_master, self.dm)
        self.assertEqual(campaign.description, "A legendary group.")
        self.assertEqual(campaign.system, self.system)
        self.assertEqual(campaign.vtt_link, "https://foundryvtt.com/game")
        self.assertEqual(campaign.video_link, "https://zoom.us/j/123456")
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

    def test_campaign_system_relationship(self) -> None:
        """
        Test the relationship between Campaign and TabletopSystem.
        """
        campaign = Campaign.objects.create(
            name="System Test Campaign",
            dungeon_master=self.dm,
            system=self.system,
        )
        self.assertEqual(campaign.system, self.system)
        self.assertIn(campaign, self.system.campaigns.all())


class CampaignCreateViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="testuser")
        self.url = reverse("campaign_create")
        self.system = TabletopSystem.objects.create(name="Pathfinder 2e")

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
        Test that a campaign is created successfully with all fields.
        """
        self.client.force_login(self.user)
        data = {
            "name": "New Adventure",
            "description": "A grand journey.",
            "system": self.system.pk,
            "vtt_link": "https://roll20.net/join/123",
            "video_link": "https://discord.gg/abc",
        }
        response = self.client.post(self.url, data)

        # Check redirection to success_url (splash)
        self.assertRedirects(response, reverse("splash"))

        # Check database
        campaign = Campaign.objects.get(name="New Adventure")
        self.assertEqual(campaign.dungeon_master, self.user)
        self.assertEqual(campaign.system, self.system)
        self.assertEqual(campaign.vtt_link, "https://roll20.net/join/123")
        self.assertEqual(campaign.video_link, "https://discord.gg/abc")

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


class CampaignListViewTests(TestCase):
    def setUp(self) -> None:
        self.user_dm, _ = UserFactory.create(username="dm")
        self.user_player, _ = UserFactory.create(username="player")
        self.managed_url = reverse("campaign_managed")
        self.joined_url = reverse("campaign_joined")

        # Create campaigns
        self.campaign1 = Campaign.objects.create(
            name="DM Campaign",
            dungeon_master=self.user_dm,
        )
        self.campaign2 = Campaign.objects.create(
            name="Player Campaign",
            dungeon_master=self.user_player,
        )
        self.campaign2.players.add(self.user_dm)

    def test_managed_list_view(self) -> None:
        """
        Test that the managed list view returns only campaigns the user DMs.
        """
        self.client.force_login(self.user_dm)
        response = self.client.get(self.managed_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/managed_campaign_list.html")
        self.assertContains(response, "DM Campaign")
        self.assertNotContains(response, "Player Campaign")

    def test_joined_list_view(self) -> None:
        """
        Test that the joined list view returns only campaigns the user is a player in.
        """
        self.client.force_login(self.user_dm)
        response = self.client.get(self.joined_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/joined_campaign_list.html")
        self.assertContains(response, "Player Campaign")
        self.assertNotContains(response, "DM Campaign")

    def test_managed_list_anonymous(self) -> None:
        """
        Test that anonymous users are redirected from managed list.
        """
        response = self.client.get(self.managed_url)
        self.assertRedirects(response, f"/users/login/?next={self.managed_url}")

    def test_joined_list_anonymous(self) -> None:
        """
        Test that anonymous users are redirected from joined list.
        """
        response = self.client.get(self.joined_url)
        self.assertRedirects(response, f"/users/login/?next={self.joined_url}")
