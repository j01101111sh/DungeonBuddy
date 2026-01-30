from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from dunbud.management.commands.populate_dev_data import (
    NUM_DEV_CAMPAIGN_MEMBERS,
    NUM_DEV_CAMPAIGNS,
    NUM_JOINED_USER_CAMPAIGNS,
    NUM_TEST_USERS,
)
from dunbud.models import Campaign

User = get_user_model()


class PopulateDevDataTests(TestCase):
    """
    Tests for the populate_dev_data management command.
    """

    @classmethod
    def setUpTestData(cls) -> None:
        """
        Run the command ONCE for the entire class.
        This significantly speeds up tests by avoiding repeated data generation.
        """
        # We suppress stdout here to keep the test runner clean
        call_command("populate_dev_data", stdout=StringIO())

    def test_command_output(self) -> None:
        """
        Test that the command runs successfully and produces the expected output.
        """
        out = StringIO()
        call_command("populate_dev_data", stdout=out)
        self.assertIn("Successfully generated development data.", out.getvalue())

    def test_data_generation_counts(self) -> None:
        """
        Test that the correct number of users and campaigns are created.
        """
        # Verify NUM_TEST_USERS generated users were created
        user_count = User.objects.filter(username__startswith="user_").count()
        self.assertEqual(user_count, NUM_TEST_USERS)

        # Verify NUM_TEST_USERS + NUM_DEV_CAMPAIGNS campaigns were created
        campaign_count = Campaign.objects.count()
        self.assertEqual(campaign_count, NUM_TEST_USERS + NUM_DEV_CAMPAIGNS)

    def test_user_associations(self) -> None:
        """
        Test that every generated user is a DM for exactly 1 campaign.
        """
        users = User.objects.filter(username__startswith="user_")

        for user in users:
            # Check DM count (should be 1 per user)
            dm_campaigns = Campaign.objects.filter(dungeon_master=user)
            self.assertEqual(
                dm_campaigns.count(),
                1,
                f"User {user.username} should DM exactly 1 campaign",
            )

            # Check Player count
            # Must be at least NUM_JOINED_USER_CAMPAIGNS (from the user-to-user logic).
            # Could be more if selected for dev campaigns.
            joined_campaigns_count = user.joined_campaigns.count()  # type: ignore[attr-defined]
            self.assertGreaterEqual(
                joined_campaigns_count,
                NUM_JOINED_USER_CAMPAIGNS,
                f"User {user.username} should be a player in at least NUM_JOINED_USER_CAMPAIGNS campaigns",
            )

    def test_dev_user_associations(self) -> None:
        """
        Test that the 'dev' user:
        1. Is a player in all user-generated campaigns.
        2. Is the DM for specific campaigns.
        """
        dev_user = User.objects.get(username="dev")

        # 1. Check Dev is DM for campaigns
        dev_dm_campaigns = Campaign.objects.filter(dungeon_master=dev_user)
        self.assertEqual(dev_dm_campaigns.count(), NUM_DEV_CAMPAIGNS)

        # Verify each of these campaigns has exactly 4 players
        for campaign in dev_dm_campaigns:
            self.assertEqual(
                campaign.players.count(),
                NUM_DEV_CAMPAIGN_MEMBERS,
                f"Dev campaign '{campaign.name}' should have exactly NUM_DEV_CAMPAIGN_MEMBERS players",
            )

        # 2. Check Dev is a player in all *user* campaigns
        # Filter campaigns where DM starts with "user_"
        user_campaigns = Campaign.objects.filter(
            dungeon_master__username__startswith="user_",
        )
        self.assertEqual(user_campaigns.count(), NUM_TEST_USERS)

        for campaign in user_campaigns:
            self.assertIn(
                dev_user,
                campaign.players.all(),
                f"Dev user should be a player in user campaign {campaign.name}",
            )
