import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from config.tests.factories import CampaignFactory, TabletopSystemFactory, UserFactory
from dunbud.models import Session


class SessionUpdateViewTest(TestCase):
    def setUp(self) -> None:
        self.dm, _ = UserFactory.create()
        self.player, _ = UserFactory.create()
        self.other_user, _ = UserFactory.create()
        self.campaign = CampaignFactory.create(
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
            players=[self.player],
        )
        self.session = Session.objects.create(
            campaign=self.campaign,
            proposer=self.dm,
            proposed_date=timezone.now() + datetime.timedelta(days=7),
            duration=4,
        )
        self.url = reverse(
            "session_edit",
            kwargs={
                "campaign_pk": self.campaign.id,
                "session_number": self.session.session_number,
            },
        )

    def test_anonymous_access(self) -> None:
        """Test that anonymous users cannot access the update view."""
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")

    def test_dm_can_access(self) -> None:
        """Test that the DM can access the update view."""
        self.client.force_login(self.dm)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "session/session_update.html")

    def test_player_cannot_access(self) -> None:
        """Test that a player in the campaign cannot access the update view."""
        self.client.force_login(self.player)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unrelated_user_cannot_access(self) -> None:
        """Test that an unrelated user cannot access the update view."""
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_dm_can_update_notes(self) -> None:
        """Test that the DM can update the session notes."""
        self.client.force_login(self.dm)
        new_notes = "Important session notes."
        new_date = self.session.proposed_date + datetime.timedelta(hours=1)
        response = self.client.post(
            self.url,
            {
                "proposed_date": new_date.strftime("%Y-%m-%dT%H:%M"),
                "duration": 5,
                "notes": new_notes,
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "session_detail",
                kwargs={
                    "campaign_pk": self.campaign.id,
                    "session_number": self.session.session_number,
                },
            ),
        )
        self.session.refresh_from_db()
        self.assertEqual(self.session.notes, new_notes)
        self.assertEqual(self.session.duration, 5)
