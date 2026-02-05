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

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(
            feed_item.message,
            "The campaign description has been updated.",
        )
        self.assertEqual(feed_item.campaign, self.campaign)

    def test_link_change_feed(self) -> None:
        """
        Test that adding a VTT link creates a feed item.
        """
        self.campaign.vtt_link = "https://example.com/vtt"
        self.campaign.save()

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "The Virtual Tabletop link was added.")

    def test_player_added_feed(self) -> None:
        """
        Test that adding a player creates a feed item.
        """
        new_player, _ = UserFactory.create(username="new_player")
        self.campaign.players.add(new_player)

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "new_player joined the party.")

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

    def test_party_feed_item_str(self) -> None:
        """
        Test that the __str__ representation includes the campaign name and message.
        """
        message_text = "The party has entered the dungeon."
        feed_item = PartyFeedItem.objects.create(
            campaign=self.campaign,
            message=message_text,
        )

        # The expected format is "{campaign.name}: {message}"
        expected_str = f"{self.campaign}: {message_text}"

        self.assertEqual(
            str(feed_item),
            expected_str,
            "PartyFeedItem __str__ should match '{campaign_name}: {message}' format.",
        )

    def test_dm_can_post_announcement(self) -> None:
        """
        Test that the Dungeon Master can post an announcement.
        """
        self.client.force_login(self.dm)
        url = reverse("campaign_announcement_create", kwargs={"pk": self.campaign.pk})
        message = "Session next Tuesday!"

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(PartyFeedItem.objects.count(), 1)
        if first_object := PartyFeedItem.objects.first():
            self.assertEqual(first_object.message, message)

    def test_player_cannot_post_announcement(self) -> None:
        """
        Test that a player in the campaign cannot post an announcement.
        """
        self.client.force_login(self.player)
        url = reverse("campaign_announcement_create", kwargs={"pk": self.campaign.pk})
        message = "I try to post."

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(PartyFeedItem.objects.count(), 0)

    def test_outsider_cannot_post_announcement(self) -> None:
        """
        Test that a user not in the campaign cannot post an announcement.
        """
        self.client.force_login(self.outsider)
        url = reverse("campaign_announcement_create", kwargs={"pk": self.campaign.pk})
        message = "Hacker post."

        response = self.client.post(url, {"message": message})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(PartyFeedItem.objects.count(), 0)
