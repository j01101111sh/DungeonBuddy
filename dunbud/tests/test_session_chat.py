from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from config.tests.factories import (
    CampaignFactory,
    SessionFactory,
    TabletopSystemFactory,
    UserFactory,
)
from dunbud.models import ChatMessage

User = get_user_model()


class SessionChatTests(TestCase):
    """
    Test suite for Session Detail page and Chat functionality.
    """

    def setUp(self) -> None:
        """
        Set up test data: User, Campaign, and Session.
        """
        self.user, self.upass = UserFactory.create()
        self.uname = self.user.get_username()
        self.o_user, self.o_upass = UserFactory.create()
        self.o_uname = self.o_user.get_username()
        self.dm, self.dmpass = UserFactory.create()
        self.dmname = self.dm.get_username()

        self.campaign = CampaignFactory.create(
            dungeon_master=self.dm,
            system=TabletopSystemFactory.create(),
        )
        self.campaign.players.add(self.user, self.o_user)

        self.session = SessionFactory.create(
            campaign=self.campaign,
        )

        self.url = reverse(
            "session_detail",
            kwargs={
                "session_number": self.session.session_number,
                "campaign_pk": self.session.campaign.pk,
            },
        )

    def test_session_detail_view_status_code(self) -> None:
        """
        Test that the session detail page returns a 200 for logged-in users.
        """
        self.client.login(username=self.uname, password=self.upass)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_access_for_non_member(self) -> None:
        """
        Test that a user not in the campaign gets a 403.
        """
        non_member, non_member_pass = UserFactory.create()
        non_member_username = non_member.get_username()
        self.client.login(username=non_member_username, password=non_member_pass)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_session_detail_context_members(self) -> None:
        """
        Test that the campaign members are correctly passed to the context.
        """
        self.client.login(username=self.uname, password=self.upass)
        response = self.client.get(self.url)

        self.assertIn("campaign_members", response.context)
        members = response.context["campaign_members"]
        self.assertEqual(members.count(), 2)
        self.assertIn(self.user, members)

    def test_post_chat_message(self) -> None:
        """
        Test posting a new chat message via the view.
        """
        self.client.login(username=self.uname, password=self.upass)
        data = {"message": "Hello Party!"}

        # Post the message
        response = self.client.post(self.url, data)

        # Should redirect back to the same page on success
        self.assertRedirects(response, self.url)

        # Verify message was saved to DB
        self.assertEqual(ChatMessage.objects.count(), 1)
        msg = ChatMessage.objects.first()
        if msg:
            self.assertEqual(msg.message, "Hello Party!")
            self.assertEqual(msg.user, self.user)
            self.assertEqual(msg.session, self.session)

    def test_chat_history_display(self) -> None:
        """
        Test that existing messages appear on the page.
        """
        ChatMessage.objects.create(
            session=self.session,
            user=self.o_user,
            message="Previous message",
        )

        self.client.login(username=self.uname, password=self.upass)
        response = self.client.get(self.url)

        self.assertContains(response, "Previous message")
        self.assertContains(response, self.o_uname)

    def test_unauthenticated_access(self) -> None:
        """
        Test that unauthenticated users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.status_code, 302)
