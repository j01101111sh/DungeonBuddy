import uuid

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import (
    PlayerCharacterFactory,
    TabletopSystemFactory,
    UserFactory,
)
from dunbud.models import Campaign

User = get_user_model()


class CampaignModelTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_user")
        self.player, _ = UserFactory.create(username="player_user")
        self.system = TabletopSystemFactory.create()

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
        self.dm, _ = UserFactory.create(username="dm_user")
        self.player, _ = UserFactory.create(username="player_user")
        self.url = reverse("campaign_create")
        self.system = TabletopSystemFactory.create()

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
        self.client.force_login(self.player)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/campaign_form.html")

    def test_create_campaign_success(self) -> None:
        """
        Test that a campaign is created successfully with all fields
        and redirects to the campaign detail page.
        """
        self.client.force_login(self.dm)
        data = {
            "name": "New Adventure",
            "description": "A grand journey.",
            "system": self.system.pk,
            "vtt_link": "https://roll20.net/join/123",
            "video_link": "https://discord.gg/abc",
        }
        response = self.client.post(self.url, data)

        # Get the created campaign
        campaign = Campaign.objects.get(name="New Adventure")

        # Check redirection to campaign detail page
        self.assertRedirects(
            response,
            reverse("campaign_detail", kwargs={"pk": campaign.pk}),
        )

        # Check database
        self.assertEqual(campaign.dungeon_master, self.dm)
        self.assertEqual(campaign.system, self.system)
        self.assertEqual(campaign.vtt_link, "https://roll20.net/join/123")
        self.assertEqual(campaign.video_link, "https://discord.gg/abc")

    def test_create_campaign_view_logs(self) -> None:
        """
        Test that the view logs the creation event.
        """
        self.client.force_login(self.player)
        data = {"name": "View Logged Campaign", "description": "Test"}

        with self.assertLogs("dunbud.views", level="INFO") as cm:
            self.client.post(self.url, data)
            self.assertTrue(
                any(
                    "Campaign created via view: View Logged Campaign" in m
                    for m in cm.output
                ),
            )

    def test_delete_player_user(self) -> None:
        """
        Test that deleting a user who is a player in a campaign removes them
        from the campaign but does not delete the campaign.
        """
        campaign = Campaign.objects.create(
            name="Player Deletion Test",
            dungeon_master=self.dm,
        )
        campaign.players.add(self.player)

        # Confirm setup
        self.assertIn(self.player, campaign.players.all())

        # Delete the player user
        self.player.delete()

        # Refresh campaign to check state
        campaign.refresh_from_db()

        # Campaign should still exist
        self.assertTrue(Campaign.objects.filter(pk=campaign.pk).exists())
        # Player should be removed
        self.assertEqual(campaign.players.count(), 0)

    def test_delete_dm_user(self) -> None:
        """
        Test that deleting a user who is the dungeon master of a campaign
        is prevented and raises a ProtectedError.
        """
        campaign = Campaign.objects.create(
            name="DM Deletion Test",
            dungeon_master=self.dm,
        )

        # Confirm setup
        self.assertTrue(Campaign.objects.filter(pk=campaign.pk).exists())

        # Deleting the DM user should raise an error
        with self.assertRaises(ProtectedError):
            self.dm.delete()


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

    def test_managed_list_empty(self) -> None:
        """
        Test that the managed list view displays a specific message when the user manages no campaigns.
        """
        # Create a user who manages no campaigns
        user_no_campaigns, _ = UserFactory.create(username="lazy_dm")
        self.client.force_login(user_no_campaigns)

        response = self.client.get(self.managed_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/managed_campaign_list.html")

        # Verify the context list is empty
        self.assertFalse(response.context["campaigns"])

        # Verify the empty state message and call-to-action from the template
        self.assertContains(response, "You are not managing any campaigns yet.")
        self.assertContains(response, "Create One")

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

    def test_joined_list_empty(self) -> None:
        """
        Test that the joined list view displays a specific message when the user has joined no campaigns.
        """
        # Create a user who has not joined any campaigns as a player
        lone_wolf, _ = UserFactory.create(username="lone_wolf")
        self.client.force_login(lone_wolf)

        response = self.client.get(self.joined_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/joined_campaign_list.html")

        # Verify the context list is empty
        self.assertFalse(response.context["campaigns"])

        # Verify the empty state message from the template
        self.assertContains(response, "You have not joined any campaigns yet.")

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


class CampaignDetailViewTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_user_detail")
        self.player, _ = UserFactory.create(username="player_user_detail")
        self.outsider, _ = UserFactory.create(username="outsider_user_detail")
        self.system = TabletopSystemFactory.create()

        self.campaign = Campaign.objects.create(
            name="Epic Quest",
            dungeon_master=self.dm,
            description="A journey to the mountain.",
            system=self.system,
            vtt_link="https://foundry.example.com",
            video_link="https://zoom.us/j/123456",
        )
        self.campaign.players.add(self.player)
        self.url = reverse("campaign_detail", kwargs={"pk": self.campaign.pk})

    def test_access_anonymous(self) -> None:
        """
        Test that anonymous users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_access_dm(self) -> None:
        """
        Test that the Dungeon Master can view the campaign details.
        """
        self.client.force_login(self.dm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/campaign_detail.html")
        self.assertContains(response, "Epic Quest")

    def test_access_player(self) -> None:
        """
        Test that a joined player can view the campaign details.
        """
        self.client.force_login(self.player)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/campaign_detail.html")
        self.assertContains(response, "Epic Quest")

    def test_player_character_name_display(self) -> None:
        """
        Test that the player's character name is displayed next to their username
        and links to the character detail page.
        """
        # Create a character for the player in this campaign
        character = PlayerCharacterFactory.create(
            user=self.player,
            campaign=self.campaign,
            name="Grog Strongjaw",
        )

        self.client.force_login(self.player)
        response = self.client.get(self.url)

        self.assertContains(response, self.player.username)

        # Build expected link URL
        char_url = reverse("character_detail", kwargs={"pk": character.pk})

        # Check that the character name appears in parenthesis and is linked
        self.assertContains(response, f'href="{char_url}"')
        self.assertContains(response, ">Grog Strongjaw</a>")

    def test_access_outsider_denied(self) -> None:
        """
        Test that a user who is neither DM nor player receives a 403 Forbidden.
        """
        self.client.force_login(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_links_display(self) -> None:
        """
        Test that VTT and video links are displayed when present.
        """
        self.client.force_login(self.dm)
        response = self.client.get(self.url)

        self.assertContains(response, "https://foundry.example.com")
        self.assertContains(response, "https://zoom.us/j/123456")
        self.assertContains(response, "Virtual Tabletop")
        self.assertContains(response, "Video Conference")

    def test_links_hidden_when_empty(self) -> None:
        """
        Test that VTT and video links are not displayed when empty.
        """
        # Clear the links
        self.campaign.vtt_link = ""
        self.campaign.video_link = ""
        self.campaign.save()

        self.client.force_login(self.dm)
        response = self.client.get(self.url)

        self.assertNotContains(
            response,
            'rel="noopener noreferrer">Virtual Tabletop</a>',
        )
        self.assertNotContains(
            response,
            'rel="noopener noreferrer">Video Conference</a>',
        )

    def test_unauthorized_access_logging(self) -> None:
        """
        Test that unauthorized access attempts are logged.
        """
        self.client.force_login(self.outsider)
        with self.assertLogs("dunbud.views", level="WARNING") as cm:
            self.client.get(self.url)
            self.assertTrue(
                any(
                    f"Unauthorized access attempt to campaign {self.campaign.pk} by user outsider_user"
                    in m
                    for m in cm.output
                ),
            )

    def test_system_name_display(self) -> None:
        """
        Test that the tabletop system name is correctly displayed on the detail page.

        This verifies that the template correctly renders the system name badge
        when a system is associated with the campaign.
        """
        # Log in as the DM to gain access to the detail view
        self.client.force_login(self.dm)

        response = self.client.get(self.url)

        # Verify the response is successful
        self.assertEqual(response.status_code, 200)

        # Verify the system name is present in the rendered HTML
        self.assertContains(response, self.system.short_name)
        # Specifically check for the badge formatting used in the template
        self.assertContains(response, 'class="badge bg-light text-primary"')

    def test_system_name_hidden_when_null(self) -> None:
        """
        Test that no system badge is displayed if the campaign has no system.
        """
        # Remove the system from the campaign
        self.campaign.system = None
        self.campaign.save()

        self.client.force_login(self.dm)
        response = self.client.get(self.url)

        # The system name should no longer be in the response
        self.assertNotContains(response, 'class="badge bg-light text-primary"')


class CampaignUpdateViewTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_update")
        self.player, _ = UserFactory.create(username="player_update")
        self.outsider, _ = UserFactory.create(username="outsider_update")
        self.system = TabletopSystemFactory.create()
        self.campaign = Campaign.objects.create(
            name="Original Campaign",
            dungeon_master=self.dm,
            description="Original Description",
            system=self.system,
            vtt_link="https://old-vtt.com",
        )
        self.campaign.players.add(self.player)
        self.url = reverse("campaign_edit", kwargs={"pk": self.campaign.pk})

    def test_access_anonymous(self) -> None:
        """
        Test that anonymous users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_access_dm_success(self) -> None:
        """
        Test that the DM can access the update page and it is pre-filled.
        """
        self.client.force_login(self.dm)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "campaign/campaign_form.html")

        # Verify form is pre-filled with existing data
        self.assertContains(response, 'value="Original Campaign"')
        self.assertContains(response, "Original Description")
        self.assertContains(response, "https://old-vtt.com")

    def test_access_player_forbidden(self) -> None:
        """
        Test that a player in the campaign cannot edit it.
        """
        self.client.force_login(self.player)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_access_outsider_forbidden(self) -> None:
        """
        Test that a user unrelated to the campaign cannot edit it.
        """
        self.client.force_login(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_update_successful(self) -> None:
        """
        Test that the DM can successfully update campaign details.
        """
        self.client.force_login(self.dm)
        new_system = TabletopSystemFactory.create()

        data = {
            "name": "Updated Campaign Name",
            "description": "Updated Description",
            "system": new_system.pk,
            "vtt_link": "https://new-vtt.com",
            "video_link": "https://new-video.com",
        }

        response = self.client.post(self.url, data)

        # Should redirect to the detail view
        self.assertRedirects(
            response,
            reverse("campaign_detail", kwargs={"pk": self.campaign.pk}),
        )

        # Verify database update
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.name, "Updated Campaign Name")
        self.assertEqual(self.campaign.description, "Updated Description")
        self.assertEqual(self.campaign.system, new_system)
        self.assertEqual(self.campaign.vtt_link, "https://new-vtt.com")
