import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from config.tests.factories import CampaignFactory, TabletopSystemFactory, UserFactory
from dunbud.forms import SessionForm
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
        self.url = reverse("session_propose", kwargs={"campaign_pk": self.campaign.pk})

    def test_proposer_is_added_to_attendees(self) -> None:
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
        self.assertIn(self.user, session.attendees.all() if session else [])

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
        self.assertIsInstance(response.context["form"], SessionForm)
        self.assertEqual(response.context["campaign"], self.campaign)

        # Verify Content
        # Check for the dynamic page header
        self.assertContains(response, f"Propose a New Session for {self.campaign.name}")

        # Check for the presence of the form fields
        self.assertContains(response, 'name="proposed_date"')
        self.assertContains(response, 'type="datetime-local"')  # Verifies the widget
        self.assertContains(response, 'name="duration"')

        # Verify the Cancel button links back to the campaign detail page
        cancel_url = reverse("campaign_detail", kwargs={"pk": self.campaign.pk})
        self.assertContains(response, f'href="{cancel_url}"')

    def test_session_form_requires_login(self) -> None:
        """
        Test that accessing the session form requires authentication.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
