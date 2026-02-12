from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import UserFactory
from dunbud.models import Campaign, PartyFeedItem

User = get_user_model()


class PartyFeedTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_feed")
        self.player, _ = UserFactory.create(username="player_feed")
        self.outsider, _ = UserFactory.create(username="outsider_feed")
        self.campaign = Campaign.objects.create(
            name="Feed Campaign",
            dungeon_master=self.dm,
            description="Initial description",
        )
        self.campaign.players.add(self.player)

    def test_description_change_feed(self) -> None:
        """
        Test that changing the description creates a feed item.
        """
        self.campaign.description = "New description"
        self.campaign.save()

        feed_item = PartyFeedItem.objects.latest("created_at")

        self.assertIsNotNone(feed_item)
        self.assertEqual(
            feed_item.message,
            "The campaign description has been updated.",
        )
        self.assertEqual(feed_item.campaign, self.campaign)
        self.assertEqual(feed_item.category, PartyFeedItem.Category.DATA_UPDATE)

    def test_link_change_feed(self) -> None:
        """
        Test that adding a VTT link creates a feed item.
        """
        self.campaign.vtt_link = "https://example.com/vtt"
        self.campaign.save()

        feed_item = PartyFeedItem.objects.latest("created_at")

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "The Virtual Tabletop link was added.")
        self.assertEqual(feed_item.category, PartyFeedItem.Category.DATA_UPDATE)

    def test_player_added_feed(self) -> None:
        """
        Test that adding a player creates a feed item.
        """
        new_player, _ = UserFactory.create(username="new_player")
        self.campaign.players.add(new_player)

        feed_item = PartyFeedItem.objects.latest("created_at")

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "new_player joined the party.")
        self.assertEqual(feed_item.category, PartyFeedItem.Category.MEMBERSHIP)

    def test_player_removed_feed(self) -> None:
        """
        Test that removing a player creates a feed item.
        """
        # Clear feed from setup
        PartyFeedItem.objects.all().delete()

        self.campaign.players.remove(self.player)

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "player_feed left the party.")
        self.assertEqual(feed_item.category, PartyFeedItem.Category.MEMBERSHIP)

    def test_party_feed_item_str(self) -> None:
        """
        Test that the __str__ representation includes the campaign name and message.
        """
        message_text = "The party has entered the dungeon."
        feed_item = PartyFeedItem.objects.create(
            campaign=self.campaign,
            message=message_text,
            category=PartyFeedItem.Category.JOURNAL,
        )

        # The expected format is "{campaign.name}: [{category}] {message}"
        expected_str = f"{self.campaign}: [journal] {message_text}"

        self.assertEqual(
            str(feed_item),
            expected_str,
            "PartyFeedItem __str__ should match '{campaign_name}: [{category}] {message}' format.",
        )

    def test_dm_can_post_announcement(self) -> None:
        """
        Test that the Dungeon Master can post an announcement.
        """
        self.client.force_login(self.dm)
        url = reverse(
            "campaign_announcement_create",
            kwargs={"slug": self.campaign.slug},
        )
        message = "Session next Tuesday!"

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 302)
        if first_object := PartyFeedItem.objects.latest("created_at"):
            self.assertEqual(first_object.message, message)
            self.assertEqual(first_object.category, PartyFeedItem.Category.ANNOUNCEMENT)

    def test_dm_cannot_post_empty_announcement(self) -> None:
        """
        Test that the Dungeon Master cannot post an empty announcement.
        """
        self.client.force_login(self.dm)
        url = reverse(
            "campaign_announcement_create",
            kwargs={"slug": self.campaign.slug},
        )

        # Snapshot count before attempt
        initial_count = PartyFeedItem.objects.count()

        # Submitting an empty message
        response = self.client.post(url, {"message": ""})

        # Should redirect back to detail view
        self.assertEqual(response.status_code, 302)

        # Ensure no feed item was created
        self.assertEqual(PartyFeedItem.objects.count(), initial_count)

    def test_player_cannot_post_announcement(self) -> None:
        """
        Test that a player in the campaign cannot post an announcement.
        """
        self.client.force_login(self.player)
        url = reverse(
            "campaign_announcement_create",
            kwargs={"slug": self.campaign.slug},
        )
        message = "I try to post."

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            PartyFeedItem.objects.filter(message=message).count(),
            0,
        )

    def test_outsider_cannot_post_announcement(self) -> None:
        """
        Test that a user not in the campaign cannot post an announcement.
        """
        self.client.force_login(self.outsider)
        url = reverse(
            "campaign_announcement_create",
            kwargs={"slug": self.campaign.slug},
        )
        message = "Hacker post."

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            PartyFeedItem.objects.filter(message=message).count(),
            0,
        )

    def test_dm_can_post_markdown_announcement(self) -> None:
        """
        Test that the Dungeon Master can post an announcement containing Markdown.
        """
        self.client.force_login(self.dm)
        url = reverse(
            "campaign_announcement_create",
            kwargs={"slug": self.campaign.slug},
        )

        markdown_message = "**Bold Announcement**\nWith a [link](https://example.com)"

        response = self.client.post(url, {"message": markdown_message})

        self.assertEqual(response.status_code, 302)
        if first_object := PartyFeedItem.objects.latest("created_at"):
            self.assertEqual(first_object.message, markdown_message)
            self.assertEqual(first_object.category, PartyFeedItem.Category.ANNOUNCEMENT)

    def test_campaign_detail_renders_markdown(self) -> None:
        """
        Test that the campaign detail view renders the markdown announcement as HTML.
        """
        self.client.force_login(self.player)

        # Create a feed item with markdown
        PartyFeedItem.objects.create(
            campaign=self.campaign,
            message="We meet at **dawn**!",
            category=PartyFeedItem.Category.ANNOUNCEMENT,
        )

        url = reverse("campaign_detail", kwargs={"slug": self.campaign.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for the rendered HTML
        self.assertContains(response, "<strong>dawn</strong>")
