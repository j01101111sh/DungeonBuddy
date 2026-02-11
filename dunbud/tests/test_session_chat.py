from campaigns.models import Campaign, ChatMessage, Session
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class SessionChatTests(TestCase):
    """
    Test suite for Session Detail page and Chat functionality.
    """

    def setUp(self) -> None:
        """
        Set up test data: User, Campaign, and Session.
        """
        self.user = User.objects.create_user(
            username="testuser",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="otheruser",
            password="password123",
        )

        self.campaign = Campaign.objects.create(
            title="Test Campaign",
            description="A test campaign",
        )
        self.campaign.members.add(self.user, self.other_user)

        self.session = Session.objects.create(
            campaign=self.campaign,
            title="Session 1",
            scheduled_time=timezone.now(),
        )

        self.url = reverse("campaigns:session_detail", kwargs={"pk": self.session.pk})

    def test_session_detail_view_status_code(self) -> None:
        """
        Test that the session detail page returns a 200 for logged-in users.
        """
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_session_detail_context_members(self) -> None:
        """
        Test that the campaign members are correctly passed to the context.
        """
        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url)

        self.assertIn("campaign_members", response.context)
        members = response.context["campaign_members"]
        self.assertEqual(members.count(), 2)
        self.assertIn(self.user, members)

    def test_post_chat_message(self) -> None:
        """
        Test posting a new chat message via the view.
        """
        self.client.login(username="testuser", password="password123")
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
            user=self.other_user,
            message="Previous message",
        )

        self.client.login(username="testuser", password="password123")
        response = self.client.get(self.url)

        self.assertContains(response, "Previous message")
        self.assertContains(response, "otheruser")

    def test_unauthenticated_access(self) -> None:
        """
        Test that unauthenticated users are redirected to login.
        """
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)
