import secrets

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from config.tests.factories import TabletopSystemFactory, UserFactory
from dunbud.models.campaign import Campaign, CampaignInvitation

User = get_user_model()


class CampaignInvitationTests(TestCase):
    """
    Test suite for Campaign Invitation features.
    """

    def setUp(self) -> None:
        """
        Set up test data: 1 DM, 1 Player, 1 Campaign.
        """
        self.dm, self.dm_pass = UserFactory.create()
        self.player, self.player_pass = UserFactory.create()
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            description="A test campaign",
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
        )
        self.client = Client()

    def test_dm_can_create_invite(self) -> None:
        """
        Verify that the DM can generate an invitation link.
        """
        self.client.login(username=self.dm.username, password=self.dm_pass)
        url = reverse("campaign_invite_create", kwargs={"pk": self.campaign.pk})

        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            CampaignInvitation.objects.filter(campaign=self.campaign).exists(),
        )
        self.assertContains(response, "Invitation link generated")

    def test_non_dm_cannot_create_invite(self) -> None:
        """
        Verify that a non-DM user cannot generate an invitation link.
        """
        self.client.login(username=self.player.username, password=self.player_pass)
        url = reverse("campaign_invite_create", kwargs={"pk": self.campaign.pk})

        response = self.client.post(url, follow=True)

        # Should redirect or error, but definitely not create an invite
        self.assertFalse(
            CampaignInvitation.objects.filter(campaign=self.campaign).exists(),
        )
        self.assertContains(response, "Only the Dungeon Master", status_code=200)

    def test_player_can_join_via_invite(self) -> None:
        """
        Verify a user can join the campaign using a valid token.
        """
        # Create invite manually
        invite = CampaignInvitation.objects.create(campaign=self.campaign)
        join_url = reverse("campaign_join", kwargs={"token": invite.token})

        self.client.login(username=self.player.username, password=self.player_pass)
        response = self.client.get(join_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.campaign.players.filter(pk=self.player.pk).exists())
        self.assertContains(
            response,
            f"You have successfully joined {self.campaign.name}",
        )

    def test_dm_cannot_join_own_campaign(self) -> None:
        """
        Verify the DM cannot join their own campaign as a player.
        """
        invite = CampaignInvitation.objects.create(campaign=self.campaign)
        join_url = reverse("campaign_join", kwargs={"token": invite.token})

        self.client.login(username=self.dm.username, password=self.dm_pass)
        response = self.client.get(join_url, follow=True)

        self.assertFalse(self.campaign.players.filter(pk=self.dm.pk).exists())
        self.assertContains(response, "You are the Dungeon Master")

    def test_invalid_token_returns_404(self) -> None:
        """
        Verify that an invalid token returns a 404 error.
        """
        self.client.login(username=self.player.username, password=self.player_pass)
        join_url = reverse(
            "campaign_join",
            kwargs={"token": f"invalid-token-{secrets.token_hex(4)}"},
        )

        response = self.client.get(join_url)
        self.assertEqual(response.status_code, 404)

    def test_inactive_invite_cannot_be_used(self) -> None:
        """
        Verify that an inactive invitation cannot be used to join.
        """
        invite = CampaignInvitation.objects.create(
            campaign=self.campaign,
            is_active=False,
        )
        join_url = reverse("campaign_join", kwargs={"token": invite.token})

        self.client.login(username=self.player.username, password=self.player_pass)
        response = self.client.get(join_url)

        # Should be 404 because get_object_or_404 filters by is_active=True
        self.assertEqual(response.status_code, 404)
