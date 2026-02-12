import datetime
from typing import cast

from django import forms
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from config.tests.factories import (
    CampaignFactory,
    PlayerCharacterFactory,
    TabletopSystemFactory,
    UserFactory,
)
from dunbud.forms.journal import JournalEntryForm
from dunbud.models.journal import JournalEntry
from dunbud.models.session import Session


class JournalModelTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create(username="journal_author")
        self.character = PlayerCharacterFactory.create(
            user=self.user,
            name="Bilbo",
        )

    def test_create_journal_entry(self) -> None:
        """
        Test that a journal entry can be created for a character.
        """
        entry = JournalEntry.objects.create(
            character=self.character,
            title="There and Back Again",
            content="A hobbit's tale.",
        )
        self.assertEqual(entry.character, self.character)
        self.assertEqual(entry.title, "There and Back Again")
        self.assertTrue(entry.created_at)

    def test_string_representation(self) -> None:
        """
        Test the string representation of the entry.
        """
        entry = JournalEntry.objects.create(
            character=self.character,
            title="My Journey",
            content="...",
        )
        self.assertEqual(str(entry), "My Journey (Bilbo)")

    def test_journal_creation_logs(self) -> None:
        """
        Test that creating a journal entry logs the event.
        """
        with self.assertLogs("dunbud.models.journal", level="INFO") as cm:
            JournalEntry.objects.create(
                character=self.character,
                title="Log Test",
                content="Content",
            )
            self.assertTrue(
                any(
                    "New journal entry created: 'Log Test' for character Bilbo" in m
                    for m in cm.output
                ),
            )


class JournalFormTests(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create()
        self.dm, _ = UserFactory.create()
        self.system = CampaignFactory.create(
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
        ).system  # Helper to get system if needed, or just ignore

        self.proposed_date = timezone.make_aware(
            datetime.datetime(2026, 1, 1, 12, 0, 0),
        )

        # Create a campaign and character
        self.campaign = CampaignFactory.create(
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
        )
        self.character = PlayerCharacterFactory.create(
            user=self.user,
            campaign=self.campaign,
        )

        # Session in the character's campaign
        self.session_valid = Session.objects.create(
            campaign=self.campaign,
            proposed_date=self.proposed_date,
            duration=4,
        )

        # Session in a different campaign
        self.other_campaign = CampaignFactory.create(
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
        )
        self.session_invalid = Session.objects.create(
            campaign=self.other_campaign,
            proposed_date=self.proposed_date,
            duration=4,
        )

    def test_form_filters_sessions(self) -> None:
        """
        Verify the form only allows selecting sessions from the character's campaign.
        """
        form = JournalEntryForm(character=self.character)
        queryset = cast(forms.ModelChoiceField, form.fields["session"]).queryset

        self.assertIn(self.session_valid, queryset)  # type: ignore[arg-type]
        self.assertNotIn(self.session_invalid, queryset)  # type: ignore[arg-type]

    def test_form_valid_data(self) -> None:
        """
        Test form validation with correct data.
        """
        data = {
            "title": "Valid Entry",
            "content": "Good content.",
            "session": self.session_valid.pk,
        }
        form = JournalEntryForm(data=data, character=self.character)
        self.assertTrue(form.is_valid())

        entry = form.save()
        self.assertEqual(entry.character, self.character)
        self.assertEqual(entry.session, self.session_valid)

    def test_form_invalid_session(self) -> None:
        """
        Test that submitting a session ID from another campaign fails validation.
        """
        data = {
            "title": "Hacking Attempt",
            "content": "Trying to link wrong session.",
            "session": self.session_invalid.pk,
        }
        form = JournalEntryForm(data=data, character=self.character)
        self.assertFalse(form.is_valid())
        self.assertIn("session", form.errors)
        self.assertIn(
            "Select a valid choice",
            str(form.errors["session"]),
        )  # Standard Django error message


class JournalViewTests(TestCase):
    def setUp(self) -> None:
        # Users
        self.owner, _ = UserFactory.create(username="owner")
        self.other_user, _ = UserFactory.create(username="stranger")

        # Data
        self.character = PlayerCharacterFactory.create(
            user=self.owner,
            name="Writer",
        )
        self.entry = JournalEntry.objects.create(
            character=self.character,
            title="First Entry",
            content="Intro",
        )

        # URLs
        self.list_url = reverse(
            "journal_list",
            kwargs={"character_id": self.character.pk},
        )
        self.create_url = reverse(
            "journal_create",
            kwargs={"character_id": self.character.pk},
        )
        self.update_url = reverse(
            "journal_update",
            kwargs={"entry_id": self.entry.pk},
        )
        self.delete_url = reverse(
            "journal_delete",
            kwargs={"entry_id": self.entry.pk},
        )

    # --- List View Tests ---

    def test_list_view_authenticated(self) -> None:
        """Test authenticated users can view the journal list."""
        self.client.force_login(self.other_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Entry")
        self.assertContains(response, "Writer")
        # Should NOT show "Write New Entry" button for non-owner
        self.assertNotContains(response, "Write New Entry")

    def test_list_view_owner_features(self) -> None:
        """Test owner sees specific controls."""
        self.client.force_login(self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Write New Entry")
        self.assertContains(response, "Edit")  # Edit button on the entry card

    def test_list_view_anonymous(self) -> None:
        """Test anonymous users are redirected."""
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f"/users/login/?next={self.list_url}")

    # --- Create View Tests ---

    def test_create_view_access_owner(self) -> None:
        """Test owner can access create page."""
        self.client.force_login(self.owner)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "journal/journal_form.html")

    def test_create_view_access_denied(self) -> None:
        """Test non-owners receive 403 Forbidden."""
        self.client.force_login(self.other_user)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 403)

    def test_create_view_submission(self) -> None:
        """Test creating a new entry via POST."""
        self.client.force_login(self.owner)
        data = {
            "title": "New Chapter",
            "content": "Exciting events.",
            "session": "",  # Optional field
        }
        response = self.client.post(self.create_url, data)

        # Verify redirect to list
        self.assertRedirects(response, self.list_url)

        # Verify DB
        self.assertTrue(JournalEntry.objects.filter(title="New Chapter").exists())

    # --- Update View Tests ---

    def test_update_view_access_owner(self) -> None:
        """Test owner can see the edit form."""
        self.client.force_login(self.owner)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "First Entry")  # Pre-filled value

    def test_update_view_access_denied(self) -> None:
        """Test non-owners cannot access edit page."""
        self.client.force_login(self.other_user)
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 403)

    def test_update_view_submission(self) -> None:
        """Test updating an entry via POST."""
        self.client.force_login(self.owner)
        data = {
            "title": "Revised Title",
            "content": "Updated content.",
            "session": "",
        }
        response = self.client.post(self.update_url, data)
        self.assertRedirects(response, self.list_url)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.title, "Revised Title")

    # --- Delete View Tests ---

    def test_delete_view_access_owner(self) -> None:
        """Test owner can access delete confirmation."""
        self.client.force_login(self.owner)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "journal/journal_confirm_delete.html")

    def test_delete_view_access_denied(self) -> None:
        """Test non-owners cannot delete."""
        self.client.force_login(self.other_user)
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 403)
        # Ensure post also fails
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 403)

    def test_delete_view_submission(self) -> None:
        """Test deleting an entry."""
        self.client.force_login(self.owner)
        response = self.client.post(self.delete_url)
        self.assertRedirects(response, self.list_url)
        self.assertFalse(JournalEntry.objects.filter(pk=self.entry.pk).exists())
        self.assertFalse(JournalEntry.objects.filter(pk=self.entry.pk).exists())
        self.assertFalse(JournalEntry.objects.filter(pk=self.entry.pk).exists())
