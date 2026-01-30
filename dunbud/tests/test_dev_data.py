from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from dunbud.models import Campaign

User = get_user_model()


class PopulateDevDataTests(TestCase):
    """
    Tests for the populate_dev_data management command.
    """

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
        call_command("populate_dev_data")

        # Verify 20 generated users were created
        user_count = User.objects.filter(username__startswith="user_").count()
        self.assertEqual(user_count, 20)

        # Verify 25 campaigns were created (20 user campaigns + 5 dev campaigns)
        campaign_count = Campaign.objects.count()
        self.assertEqual(campaign_count, 25)

    def test_user_associations(self) -> None:
        """
        Test that every generated user is a DM for exactly 1 campaign.
        Note: Player count check is relaxed/modified because users can now be
        players in Dev campaigns in addition to the base 3.
        """
        call_command("populate_dev_data")

        users = User.objects.filter(username__startswith="user_")

        for user in users:
            # Check DM count (should still be 1 per user)
            dm_campaigns = Campaign.objects.filter(dungeon_master=user)
            self.assertEqual(
                dm_campaigns.count(),
                1,
                f"User {user.username} should DM exactly 1 campaign",
            )

            # Check Player count
            # Must be at least 3 (from the user-to-user logic).
            # Could be more if selected for dev campaigns.
            joined_campaigns_count = user.joined_campaigns.count()  # type: ignore[attr-defined]
            self.assertGreaterEqual(
                joined_campaigns_count,
                3,
                f"User {user.username} should be a player in at least 3 campaigns",
            )

    def test_dev_user_associations(self) -> None:
        """
        Test that the 'dev' user:
        1. Is a player in all 20 user-generated campaigns.
        2. Is the DM for 5 specific campaigns.
        """
        call_command("populate_dev_data")

        dev_user = User.objects.get(username="dev")

        # 1. Check Dev is DM for 5 campaigns
        dev_dm_campaigns = Campaign.objects.filter(dungeon_master=dev_user)
        self.assertEqual(dev_dm_campaigns.count(), 5)

        # Verify each of these 5 campaigns has exactly 4 players
        for campaign in dev_dm_campaigns:
            self.assertEqual(
                campaign.players.count(),
                4,
                f"Dev campaign '{campaign.name}' should have exactly 4 players",
            )

        # 2. Check Dev is a player in all *user* campaigns
        # Filter campaigns where DM starts with "user_"
        user_campaigns = Campaign.objects.filter(
            dungeon_master__username__startswith="user_",
        )
        self.assertEqual(user_campaigns.count(), 20)

        for campaign in user_campaigns:
            self.assertIn(
                dev_user,
                campaign.players.all(),
                f"Dev user should be a player in user campaign {campaign.name}",
            )
