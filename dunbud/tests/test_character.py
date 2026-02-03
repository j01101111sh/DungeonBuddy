from django.test import TestCase
from django.urls import reverse

from config.tests.factories import PlayerCharacterFactory, UserFactory
from dunbud.models import Campaign, PlayerCharacter


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
        character = PlayerCharacter.objects.create(
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
        character = PlayerCharacter.objects.create(
            user=self.user,
            name="Gimli",
            campaign=self.campaign,
        )
        self.assertEqual(character.campaign, self.campaign)
        self.assertIn(character, self.campaign.player_characters.all())

    def test_character_creation_logs(self) -> None:
        """
        Test that creating a character logs the event.
        """
        with self.assertLogs("dunbud.models.character", level="INFO") as cm:
            PlayerCharacter.objects.create(user=self.user, name="Legolas")
            self.assertTrue(
                any("New character created: Legolas" in m for m in cm.output),
            )


class CharacterViewTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="view_user")
        self.other_user, _ = UserFactory.create(username="other_user")
        self.client.force_login(self.user)

    def test_character_list_empty(self) -> None:
        """
        Test that the character list view renders correctly when the user has no characters.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("character_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "character/character_list.html")

        # Verify the context list is empty
        # 'object_list' is always present in ListView
        self.assertFalse(response.context["object_list"])

        # 'characters' is present because context_object_name="characters" in the view
        self.assertFalse(response.context["characters"])

        # Verify user-friendly empty state message matches your template
        self.assertContains(response, "You haven't created any characters yet")

    def test_character_detail_sheet_link(self) -> None:
        """
        Test that the external character sheet link is displayed when present.
        """
        # Create a character with a sheet link
        character = PlayerCharacterFactory.create(
            user=self.user,
            name="Link Tester",
            character_sheet_link="https://dndbeyond.com/characters/12345",
        )
        url = reverse("character_detail", kwargs={"pk": character.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Verify the link URL is present
        self.assertContains(response, "https://dndbeyond.com/characters/12345")

        # Verify the label/text is present (matches the template update)
        self.assertContains(response, "Character sheet link")

    def test_character_list_with_campaign(self) -> None:
        """
        Test that the character list displays the campaign name for assigned characters.
        """
        # 1. Setup: Create a campaign
        # We need a DM for the campaign, using self.user or creating a new one works
        dm_user, _ = UserFactory.create(username="dm_user")
        campaign = Campaign.objects.create(
            name="The Fellowship",
            dungeon_master=dm_user,
        )

        # 2. Setup: Create a character linked to that campaign
        # Assuming 'self.user' was created in setUp()
        if not hasattr(self, "user"):
            self.user, _ = UserFactory.create(username="test_user_w_campaign")

        self.client.force_login(self.user)

        _ = PlayerCharacterFactory.create(
            user=self.user,
            name="Frodo",
            campaign=campaign,
        )

        # 3. Action: Get the list view
        response = self.client.get(
            reverse("character_list"),
        )  # Ensure self.url is set to reverse("character_list")

        # 4. Assertion: Check for character and campaign info
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frodo")

        # Verify the specific campaign line from the template is rendered
        # Template: Campaign: {{ character.campaign.name }}
        self.assertContains(response, "Campaign: The Fellowship")

    def test_character_list_view(self) -> None:
        """
        Test that the list view shows only the user's characters.
        """
        c1 = PlayerCharacterFactory.create(user=self.user, name="My Char")
        PlayerCharacterFactory.create(user=self.other_user, name="Other Char")

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
        character = PlayerCharacter.objects.get(name="New Hero")
        self.assertRedirects(
            response,
            reverse("character_detail", kwargs={"pk": character.pk}),
        )
        self.assertEqual(character.user, self.user)

    def test_character_update_view_access(self) -> None:
        """
        Test that only the owner can edit the character.
        """
        char = PlayerCharacterFactory.create(user=self.user)
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

        char = PlayerCharacterFactory.create(user=self.user, campaign=campaign)
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
