import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import FormMixin

from dunbud.forms import ChatMessageForm
from dunbud.models import Session

logger = logging.getLogger(__name__)


class SessionDetailView(LoginRequiredMixin, FormMixin, DetailView):
    """
    View to display session details, a list of campaign members,
    and a chat interface.
    """

    model = Session
    template_name = "session/session_detail.html"
    context_object_name = "session_obj"
    form_class = ChatMessageForm

    def get_success_url(self) -> str:
        """
        Returns the URL to redirect to after a successful form submission.
        """
        return reverse("session:session_detail", kwargs={"pk": self.object.pk})

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
