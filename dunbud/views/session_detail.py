import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin

from dunbud.forms import ChatMessageForm
from dunbud.models import Session

logger = logging.getLogger(__name__)


class SessionDetailView(LoginRequiredMixin, UserPassesTestMixin, FormMixin, DetailView):
    """
    View to display session details using Campaign ID and Session Number lookup.
    """

    model = Session
    template_name = "session/session_detail.html"
    context_object_name = "session_obj"
    form_class = ChatMessageForm

    def test_func(self) -> bool:
        """
        Ensure only the DM or campaign players can view the session.
        """
        session = self.get_object()
        user = self.request.user
        if session.campaign.dungeon_master == user:
            return True
        if user.pk is None:
            return False
        return session.campaign.players.filter(pk=user.pk).exists()

    def get_object(self, queryset: Any = None) -> Session | Any:
        """
        Retrieve the Session object based on campaign_slug and session_number
        from the URL.
        """
        if queryset is None:
            queryset = self.get_queryset()

        campaign_slug = self.kwargs.get("campaign_slug")
        session_number = self.kwargs.get("session_number")

        return get_object_or_404(
            queryset,
            campaign__slug=campaign_slug,
            session_number=session_number,
        )

    def get_success_url(self) -> str:
        """
        Redirects back to the same page using the new URL parameters.
        """
        return reverse(
            "session_detail",
            kwargs={
                "campaign_slug": self.object.campaign.slug,
                "session_number": self.object.session_number,
            },
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """
        Adds campaign members and chat messages to the context.
        """
        context = super().get_context_data(**kwargs)

        # Explicitly typing the session object for stricter checking if needed
        session: Session = self.object

        # Add campaign members
        context["campaign_members"] = session.campaign.players.all()

        # Add chat history
        context["chat_messages"] = session.chat_messages.select_related("user").all()

        # Add the form
        context["form"] = self.get_form()

        logger.info(
            "User %s accessing session detail for Session %s",
            self.request.user.id,
            session.id,
        )
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        Handles the POST request for sending a chat message.
        """
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form: ChatMessageForm) -> HttpResponse:
        """
        Saves the chat message with the current user and session.
        """
        message = form.save(commit=False)
        message.user = self.request.user
        message.session = self.object
        message.save()

        logger.info(
            "User %s posted a message in Session %s",
            self.request.user.id,
            self.object.id,
        )
        return super().form_valid(form)
