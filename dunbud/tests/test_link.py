from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import HelpfulLinkFactory, UserFactory
from dunbud.models import Campaign, HelpfulLink
from dunbud.models.links import MAX_LINKS_PER_CAMPAIGN

User = get_user_model()


class HelpfulLinkTests(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create(username="dm_user_link")
        self.player, _ = UserFactory.create(username="player_user_link")
        self.outsider, _ = UserFactory.create(username="outsider_user_link")
        self.campaign = Campaign.objects.create(
            name="Link Test Campaign",
            dungeon_master=self.dm,
        )
        self.campaign.players.add(self.player)
        self.add_url = reverse("helpful_link_add", kwargs={"slug": self.campaign.slug})
        self.campaign_url = reverse(
            "campaign_detail",
            kwargs={"slug": self.campaign.slug},
        )

    def test_dm_can_add_link(self) -> None:
        """
        Test that the Dungeon Master can add a helpful link.
        """
        self.client.force_login(self.dm)
        data = {"name": "Test Link", "url": "https://test.com"}
        response = self.client.post(
            self.add_url,
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(name="Test Link")
            .exists(),
        )
        self.assertEqual(response.json()["name"], "Test Link")

    def test_add_link_without_protocol(self) -> None:
        """
        Test that adding a link without a protocol ('http://' or 'https://')
        results in 'https://' being prepended.
        """
        self.client.force_login(self.dm)
        data = {"name": "No Protocol Link", "url": "google.com"}
        response = self.client.post(
            self.add_url,
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(name="No Protocol Link")
            .exists(),
        )
        link = HelpfulLink.objects.get(name="No Protocol Link")
        self.assertEqual(link.url, "https://google.com")
        self.assertEqual(response.json()["url"], "https://google.com")

    def test_player_cannot_add_link(self) -> None:
        """
        Test that a player cannot add a helpful link.
        """
        self.client.force_login(self.player)
        data = {"name": "Player Link", "url": "https://player.com"}
        response = self.client.post(
            self.add_url,
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(name="Player Link")
            .exists(),
        )

    def test_outsider_cannot_add_link(self) -> None:
        """
        Test that an outsider cannot add a helpful link.
        """
        self.client.force_login(self.outsider)
        data = {"name": "Outsider Link", "url": "https://outsider.com"}
        response = self.client.post(
            self.add_url,
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(name="Outsider Link")
            .exists(),
        )

    def test_link_limit_is_enforced(self) -> None:
        """
        Test that no more than MAX_LINKS_PER_CAMPAIGN links can be added.
        """
        self.client.force_login(self.dm)
        for i in range(MAX_LINKS_PER_CAMPAIGN):
            HelpfulLinkFactory.create(campaign=self.campaign, name=f"Link {i}")
        self.assertEqual(
            HelpfulLink.objects.filter(campaign=self.campaign).count(),
            MAX_LINKS_PER_CAMPAIGN,
        )

        data = {"name": "MAX_LINKS_PER_CAMPAIGN+1 Link", "url": "https://toomany.com"}
        response = self.client.post(
            self.add_url,
            data,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            f"You can only add up to {MAX_LINKS_PER_CAMPAIGN} helpful links per campaign.",
            response.json()["errors"]["__all__"][0],
        )
        self.assertFalse(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(name="MAX_LINKS_PER_CAMPAIGN+1 Link")
            .exists(),
        )
        self.assertEqual(
            HelpfulLink.objects.filter(campaign=self.campaign).count(),
            MAX_LINKS_PER_CAMPAIGN,
        )

    def test_dm_can_delete_link(self) -> None:
        """
        Test that the Dungeon Master can delete a helpful link.
        """
        link = HelpfulLinkFactory.create(campaign=self.campaign)
        delete_url = reverse("helpful_link_delete", kwargs={"pk": link.pk})
        self.client.force_login(self.dm)
        response = self.client.post(
            delete_url,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Link deleted successfully.")
        self.assertFalse(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(pk=link.pk)
            .exists(),
        )

    def test_player_cannot_delete_link(self) -> None:
        """
        Test that a player cannot delete a helpful link.
        """
        link = HelpfulLinkFactory.create(campaign=self.campaign)
        delete_url = reverse("helpful_link_delete", kwargs={"pk": link.pk})
        self.client.force_login(self.player)
        response = self.client.post(
            delete_url,
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            HelpfulLink.objects.filter(campaign=self.campaign)
            .filter(pk=link.pk)
            .exists(),
        )

    def test_links_are_displayed(self) -> None:
        """
        Test that helpful links are displayed on the campaign detail page.
        """
        link = HelpfulLinkFactory.create(campaign=self.campaign)
        self.client.force_login(self.dm)
        response = self.client.get(self.campaign_url)
        self.assertContains(response, link.name)
        self.assertContains(response, link.url)

    def test_string_representation(self) -> None:
        """
        Test the string representation of the HelpfulLink model.
        """
        link = HelpfulLinkFactory.create(
            name="My Link",
            campaign=self.campaign,
        )
        self.assertEqual(str(link), "My Link")
