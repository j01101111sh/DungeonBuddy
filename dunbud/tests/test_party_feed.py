from django.contrib.auth import get_user_model
from django.test import TestCase

from config.tests.factories import UserFactory
from dunbud.models import Campaign, PartyFeedItem

User = get_user_model()


class PartyFeedTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_feed")
        self.player, _ = UserFactory.create(username="player_feed")
        self.campaign = Campaign.objects.create(
            name="Feed Campaign",
            dungeon_master=self.dm,
            description="Initial description",
        )

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
        self.campaign.players.add(self.player)

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "player_feed joined the party.")

    def test_player_removed_feed(self) -> None:
        """
        Test that removing a player creates a feed item.
        """
        self.campaign.players.add(self.player)
        # Clear feed from addition
        PartyFeedItem.objects.all().delete()

        self.campaign.players.remove(self.player)

        feed_item = PartyFeedItem.objects.first()

        if not feed_item:
            raise AssertionError

        self.assertIsNotNone(feed_item)
        self.assertEqual(feed_item.message, "player_feed left the party.")
