import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from config.tests.factories import CampaignFactory, TabletopSystemFactory, UserFactory
from dunbud.forms import SessionCreateForm
from dunbud.models import Session


class SessionModelTest(TestCase):
    def setUp(self) -> None:
        self.user, self.upass = UserFactory.create()
        self.campaign = CampaignFactory.create(
            dungeon_master=self.user,
            system=TabletopSystemFactory.create(),
        )
        self.proposed_date = timezone.now() + datetime.timedelta(days=7)
        self.session = Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=self.proposed_date,
            duration=4,
        )

    def test_session_str(self) -> None:
        self.assertEqual(
            str(self.session),
            f"Session for {self.campaign.name} at {self.proposed_date}",
        )

    def test_session_creation(self) -> None:
        self.assertIsInstance(self.session, Session)
        self.assertEqual(self.session.campaign, self.campaign)
        self.assertEqual(self.session.proposer, self.user)
        self.assertEqual(self.session.proposed_date, self.proposed_date)
        self.assertEqual(self.session.duration, 4)
        self.assertEqual(self.session.attendees.count(), 0)
        self.assertEqual(self.session.busy_users.count(), 0)
        self.assertEqual(self.session.session_number, 1)

    def test_session_number_sequential(self) -> None:
        """Test that session numbers increment sequentially."""
        session2 = Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=self.proposed_date + datetime.timedelta(days=7),
            duration=4,
        )
        self.assertEqual(session2.session_number, 2)

        session3 = Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=self.proposed_date + datetime.timedelta(days=14),
            duration=4,
        )
        self.assertEqual(session3.session_number, 3)

    def test_session_number_independent_campaigns(self) -> None:
        """Test that session numbering is independent per campaign."""
        other_campaign = CampaignFactory.create(
            dungeon_master=self.user,
            system=TabletopSystemFactory.create(),
        )

        # Create session for other campaign
        other_session = Session.objects.create(
            campaign=other_campaign,
            proposer=self.user,
            proposed_date=self.proposed_date,
            duration=4,
        )

        # Should start at 1
        self.assertEqual(other_session.session_number, 1)

        # Original campaign should still be at 1 (from setUp)
        self.assertEqual(self.session.session_number, 1)

        # Add another to original
        session2 = Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=self.proposed_date,
            duration=4,
        )
        self.assertEqual(session2.session_number, 2)

    def test_proposer_deletion(self) -> None:
        """Test that if a proposer is deleted, the session's proposer is set to NULL."""
        proposer_user, _ = UserFactory.create()
        session = Session.objects.create(
            campaign=self.campaign,
            proposer=proposer_user,
            proposed_date=self.proposed_date,
            duration=4,
        )
        self.assertEqual(session.proposer, proposer_user)
        proposer_user.delete()
        session.refresh_from_db()
        self.assertIsNone(session.proposer)


class SessionCreateViewTest(TestCase):
    def setUp(self) -> None:
        self.user, self.upass = UserFactory.create()
        self.campaign = CampaignFactory.create(
            dungeon_master=self.user,
            system=TabletopSystemFactory.create(),
        )
        self.client.force_login(self.user)
        self.url = reverse(
            "session_propose",
            kwargs={"campaign_slug": self.campaign.slug},
        )

    def test_dm_is_added_to_attendees(self) -> None:
        """Test that the DM is automatically added to the attendees list."""
        self.assertEqual(Session.objects.count(), 0)
        proposed_date = timezone.now() + datetime.timedelta(days=7)
        response = self.client.post(
            self.url,
            {
                "proposed_date": proposed_date.strftime("%Y-%m-%dT%H:%M"),
                "duration": 4,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Session.objects.count(), 1)
        session = Session.objects.first()
        self.assertTrue(session)
        # In this setup, user is DM.
        self.assertIn(self.user, session.attendees.all() if session else [])

    def test_proposer_and_dm_added(self) -> None:
        """Test that if a player proposes, both they and the DM are added."""
        player, _ = UserFactory.create()
        self.campaign.players.add(player)
        self.client.force_login(player)

        proposed_date = timezone.now() + datetime.timedelta(days=7)
        self.client.post(
            self.url,
            {
                "proposed_date": proposed_date.strftime("%Y-%m-%dT%H:%M"),
                "duration": 4,
            },
        )

        session = Session.objects.first()
        self.assertTrue(session)
        self.assertIn(self.user, session.attendees.all() if session else [])  # DM
        self.assertIn(player, session.attendees.all() if session else [])  # Proposer

    def test_session_form_renders_correctly(self) -> None:
        """
        Test that the session form renders with the correct context, status code,
        and HTML content.
        """
        response = self.client.get(self.url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "session/session_form.html")

        # Verify Context
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], SessionCreateForm)
        self.assertEqual(response.context["campaign"], self.campaign)

        # Verify Content
        self.assertContains(response, f"Propose a New Session for {self.campaign.name}")
        self.assertContains(response, 'name="proposed_date"')
        self.assertContains(response, 'type="datetime-local"')
        self.assertContains(response, 'name="duration"')

        cancel_url = reverse("campaign_detail", kwargs={"slug": self.campaign.slug})
        self.assertContains(response, f'href="{cancel_url}"')

    def test_session_form_requires_login(self) -> None:
        """
        Test that accessing the session form requires authentication.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)


class TestProposedSessionsDisplay(TestCase):
    def setUp(self) -> None:
        self.user, _ = UserFactory.create()
        self.system = TabletopSystemFactory.create()
        self.campaign = CampaignFactory.create(
            dungeon_master=self.user,
            system=self.system,
            players=[self.user],
        )
        self.client.force_login(self.user)
        self.url = reverse("campaign_detail", kwargs={"slug": self.campaign.slug})

    def test_proposed_sessions_are_shown(self) -> None:
        """
        GIVEN a campaign with proposed sessions
        WHEN a user views the campaign detail page
        THEN they see the proposed sessions listed.
        """
        now = timezone.now()
        Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=now,
            duration=4,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proposed Sessions")
        self.assertNotContains(response, "No sessions proposed yet")
        self.assertContains(response, now.strftime("%B"))
        self.assertContains(response, str(now.day))
        self.assertContains(response, str(now.year))

    def test_no_proposed_sessions_message(self) -> None:
        """
        GIVEN a campaign with no proposed sessions
        WHEN a user views the campaign detail page
        THEN they do not see the proposed sessions section.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proposed Sessions")
        self.assertContains(response, "No sessions proposed yet")


class SessionToggleAttendanceViewTest(TestCase):
    def setUp(self) -> None:
        self.user, self.upass = UserFactory.create()
        self.other_user, _ = UserFactory.create()
        self.campaign = CampaignFactory.create(
            dungeon_master=self.user,
            system=TabletopSystemFactory.create(),
            players=[self.user, self.other_user],
        )
        self.session = Session.objects.create(
            campaign=self.campaign,
            proposer=self.user,
            proposed_date=timezone.now() + datetime.timedelta(days=7),
            duration=4,
        )
        self.session.attendees.add(self.user)
        self.url = reverse("session_toggle_attendance", kwargs={"pk": self.session.pk})

    def test_toggle_attendance_requires_login(self) -> None:
        """
        Test that toggling attendance requires authentication.
        """
        self.client.logout()
        response = self.client.post(self.url)
        login_url = reverse("login")
        expected_url = f"{login_url}?next={self.url}"
        self.assertRedirects(response, expected_url)

    def test_toggle_attendance_for_non_existent_session(self) -> None:
        """
        Test that toggling attendance for a non-existent session returns a 404.
        """
        self.client.force_login(self.user)
        url = reverse("session_toggle_attendance", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_add_user_to_attendees_if_new(self) -> None:
        """
        Test that a user is added to attendees if they are in neither list.
        """
        self.client.force_login(self.other_user)
        self.assertNotIn(self.other_user, self.session.attendees.all())
        self.assertNotIn(self.other_user, self.session.busy_users.all())

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.session.refresh_from_db()
        self.assertIn(self.other_user, self.session.attendees.all())
        self.assertNotIn(self.other_user, self.session.busy_users.all())

    def test_move_attendee_to_busy(self) -> None:
        """
        Test that an attendee is moved to busy_users when toggled.
        """
        self.client.force_login(self.user)
        self.assertIn(self.user, self.session.attendees.all())

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.session.refresh_from_db()
        self.assertNotIn(self.user, self.session.attendees.all())
        self.assertIn(self.user, self.session.busy_users.all())

    def test_move_busy_to_attendee(self) -> None:
        """
        Test that a busy user is moved to attendees when toggled.
        """
        self.session.attendees.remove(self.user)
        self.session.busy_users.add(self.user)
        self.client.force_login(self.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.session.refresh_from_db()
        self.assertIn(self.user, self.session.attendees.all())
        self.assertNotIn(self.user, self.session.busy_users.all())
