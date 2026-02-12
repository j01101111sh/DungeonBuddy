from typing import cast

from django import forms
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import UserFactory
from dunbud.models import Campaign, JournalEntry, PlayerCharacter


class JournalTests(TestCase):
    """
    Test suite for Journal Entry functionality.
    """

    def setUp(self) -> None:
        self.user, _ = UserFactory.create()
        self.o_user, _ = UserFactory.create()
        self.dm, _ = UserFactory.create()
        self.campaign = Campaign.objects.create(
            name="Test Campaign",
            dungeon_master=self.dm,
        )
        self.character = PlayerCharacter.objects.create(
            name="Test Char",
            user=self.user,
            campaign=self.campaign,
        )
        self.entry = JournalEntry.objects.create(
            character=self.character,
            title="Old Entry",
            content="Old content",
        )

    def test_create_journal_entry(self) -> None:
        """
        Verify that a user can create a journal entry for their character.
        """
        self.client.force_login(self.user)
        url = reverse(
            "journal_create",
            kwargs={"character_id": self.character.pk},
        )
        data = {
            "title": "My New Adventure",
            "content": "We fought a dragon.",
        }
        response = self.client.post(url, data)
        self.assertRedirects(
            response,
            reverse("journal_list", kwargs={"character_id": self.character.pk}),
        )
        self.assertTrue(JournalEntry.objects.filter(title="My New Adventure").exists())

    def test_journal_permissions(self) -> None:
        """
        Verify that a user cannot create/edit a journal for a character they do not own.
        """
        self.client.force_login(self.o_user)

        # Try to access create page
        url_create = reverse(
            "journal_create",
            kwargs={"character_id": self.character.pk},
        )
        response_create = self.client.get(url_create)
        self.assertEqual(response_create.status_code, 403)

        # Try to edit existing entry
        url_edit = reverse(
            "journal_update",
            kwargs={"entry_id": self.entry.pk},
        )
        response_edit = self.client.post(
            url_edit,
            {"title": "Hacked", "content": "Bad"},
        )
        self.assertEqual(response_edit.status_code, 403)
        self.entry.refresh_from_db()
        self.assertNotEqual(self.entry.title, "Hacked")

    def test_filter_sessions_in_form(self) -> None:
        """
        Verify the form only shows sessions from the character's campaign.
        """
        from dunbud.forms.journal import JournalEntryForm
        from dunbud.models.session import Session

        # Session in this campaign
        session_valid = Session.objects.create(
            campaign=self.campaign,
            proposed_date="2026-01-01 12:00:00",
            duration=2,
        )
        # Session in another campaign
        other_campaign = Campaign.objects.create(
            name="Other Campaign",
            dungeon_master=self.o_user,
        )
        session_invalid = Session.objects.create(
            campaign=other_campaign,
            proposed_date="2026-01-01 12:00:00",
            duration=2,
        )

        form = JournalEntryForm(character=self.character)
        session_field = cast(forms.ModelChoiceField, form.fields["session"])
        if session_field.queryset is not None:
            self.assertIn(session_valid, session_field.queryset)
            self.assertNotIn(session_invalid, session_field.queryset)
