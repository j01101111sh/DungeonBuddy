from django.test import TestCase
from django.urls import reverse

from config.tests.factories import CharacterFactory, UserFactory
from dunbud.models import Campaign, Character


class CharacterModelTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="char_owner")
        self.dm, _ = UserFactory.create(username="dm_user")
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            dungeon_master=self.dm,
        )

    def test_create_character(self) -> None:
        """
        Test that a character can be created with basic attributes.
        """
        character = Character.objects.create(
            user=self.user,
            name="Aragorn",
            race="Human",
            character_class="Ranger",
            level=5,
        )
        self.assertEqual(character.name, "Aragorn")
        self.assertEqual(character.user, self.user)
        self.assertEqual(character.level, 5)

    def test_add_character_to_campaign(self) -> None:
        """
        Test linking a character to a campaign.
        """
        character = Character.objects.create(
            user=self.user,
            name="Gimli",
            campaign=self.campaign,
        )
        self.assertEqual(character.campaign, self.campaign)
        self.assertIn(character, self.campaign.characters.all())

    def test_character_creation_logs(self) -> None:
        """
        Test that creating a character logs the event.
        """
        with self.assertLogs("dunbud.models.character", level="INFO") as cm:
            Character.objects.create(user=self.user, name="Legolas")
            self.assertTrue(
                any("New character created: Legolas" in m for m in cm.output),
            )


class CharacterViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="view_user")
        self.other_user, _ = UserFactory.create(username="other_user")
        self.client.force_login(self.user)

    def test_character_list_view(self) -> None:
        """
        Test that the list view shows only the user's characters.
        """
        c1 = CharacterFactory.create(user=self.user, name="My Char")
        CharacterFactory.create(user=self.other_user, name="Other Char")

        response = self.client.get(reverse("character_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, c1.name)
        self.assertNotContains(response, "Other Char")

    def test_character_create_view(self) -> None:
        """
        Test creating a character via the view.
        """
        url = reverse("character_create")
        data = {
            "name": "New Hero",
            "race": "Elf",
            "character_class": "Wizard",
            "level": 1,
            "bio": "Test bio",
        }
        response = self.client.post(url, data)

        # Should redirect to detail view
        character = Character.objects.get(name="New Hero")
        self.assertRedirects(
            response,
            reverse("character_detail", kwargs={"pk": character.pk}),
        )
        self.assertEqual(character.user, self.user)

    def test_character_update_view_access(self) -> None:
        """
        Test that only the owner can edit the character.
        """
        char = CharacterFactory.create(user=self.user)
        url = reverse("character_edit", kwargs={"pk": char.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Try to access as other user
        self.client.force_login(self.other_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_character_detail_view_permissions(self) -> None:
        """
        Test visibility rules for character details.
        """
        dm, _ = UserFactory.create(username="dm")
        player, _ = UserFactory.create(username="player")
        outsider, _ = UserFactory.create(username="outsider")

        campaign = Campaign.objects.create(name="Camp", dungeon_master=dm)
        campaign.players.add(player)

        char = CharacterFactory.create(user=self.user, campaign=campaign)
        url = reverse("character_detail", kwargs={"pk": char.pk})

        # Owner can view
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)

        # DM of campaign can view
        self.client.force_login(dm)
        self.assertEqual(self.client.get(url).status_code, 200)

        # Player in campaign can view
        self.client.force_login(player)
        self.assertEqual(self.client.get(url).status_code, 200)

        # Outsider cannot view
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(url).status_code, 403)
