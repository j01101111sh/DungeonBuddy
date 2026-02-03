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

    def test_string_representation(self) -> None:
        """
        Test that the string representation of a PlayerCharacter is its name.
        """
        # Define a specific name for the character
        character_name: str = "Grog Strongjaw"

        # Create a character instance using the factory
        character = PlayerCharacterFactory.create(
            user=self.user,
            name=character_name,
        )

        # Assert that the __str__ method returns the character's name
        self.assertEqual(str(character), character_name)
        # Explicitly check that it matches the name field
        self.assertEqual(str(character), character.name)


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

    def test_character_update_view_get_success_url(self) -> None:
        """
        Test that get_success_url correctly redirects to the character's detail page.
        """
        # Create a character owned by the logged-in user
        character = PlayerCharacterFactory.create(user=self.user, name="Old Name")
        url = reverse("character_edit", kwargs={"pk": character.pk})

        # Define the update data
        data = {
            "name": "Updated Name",
            "race": character.race,
            "character_class": character.character_class,
            "level": character.level,
            "bio": character.bio,
        }

        # Perform the update
        response = self.client.post(url, data)

        # Verify that the response is a redirect to the character_detail view
        # This confirms get_success_url returned the expected URL
        expected_url = reverse("character_detail", kwargs={"pk": character.pk})
        self.assertRedirects(response, expected_url)

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

    def test_character_list_view_anonymous(self) -> None:
        """
        Test that an anonymous user is redirected to the login page.
        """
        # Ensure the client is logged out
        self.client.logout()
        url = reverse("character_list")

        response = self.client.get(url)

        # LoginRequiredMixin redirects to the settings.LOGIN_URL with a 'next' parameter
        # Based on your urls.py, the login path is /users/login/
        expected_url = f"{reverse('login')}?next={url}"

        self.assertRedirects(
            response,
            expected_url,
            msg_prefix="Anonymous users must be redirected to the login page.",
        )

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


class CharacterCreateFormTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="builder")
        self.url = reverse("character_create")

        # Create a campaign to test the dropdown selection
        self.campaign_dm, _ = UserFactory.create(username="dungeon_master")
        self.campaign = Campaign.objects.create(
            name="Curse of Strahd",
            dungeon_master=self.campaign_dm,
        )

    def test_access_anonymous(self) -> None:
        """
        Test that anonymous users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/users/login/?next={self.url}")

    def test_create_form_renders(self) -> None:
        """
        Test that the creation page renders the correct template and fields.
        """
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "character/character_form.html")

        # Verify common fields are present in the HTML
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="character_class"')
        self.assertContains(response, 'name="level"')
        # Verify the campaign dropdown contains our created campaign
        self.assertContains(response, self.campaign.name)

    def test_create_character_success(self) -> None:
        """
        Test that submitting valid data creates a character assigned to the current user.
        """
        self.client.force_login(self.user)

        data = {
            "name": "Vax'ildan",
            "race": "Half-Elf",
            "character_class": "Rogue",
            "level": 5,
            "bio": "Dagger, dagger, dagger.",
            "campaign": self.campaign.pk,
            # "character_sheet_link": "..." # Include this if you added the field earlier
        }

        response = self.client.post(self.url, data)

        # Verify redirection to the detail page
        new_char = PlayerCharacter.objects.get(name="Vax'ildan")
        self.assertRedirects(
            response,
            reverse("character_detail", kwargs={"pk": new_char.pk}),
        )

        # Verify Database Integrity
        self.assertEqual(new_char.user, self.user)
        self.assertEqual(new_char.character_class, "Rogue")
        self.assertEqual(new_char.campaign, self.campaign)

    def test_create_character_invalid(self) -> None:
        """
        Test that submitting invalid data (missing required name) shows errors.
        """
        self.client.force_login(self.user)

        data = {
            "name": "",  # Name is required
            "race": "Human",
            "character_class": "Fighter",
            "level": 1,
        }

        response = self.client.post(self.url, data)

        # Should stay on the same page (200 OK)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "character/character_form.html")

        # Check for form error
        form = response.context["form"]
        self.assertTrue(form.errors)
        self.assertIn("name", form.errors)
        self.assertContains(response, "This field is required")
