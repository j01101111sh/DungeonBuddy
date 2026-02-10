import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from config.tests.factories import CampaignFactory, TabletopSystemFactory, UserFactory
from dunbud.models import Session


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
