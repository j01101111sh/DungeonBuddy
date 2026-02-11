import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import UpdateView

from dunbud.forms.session import SessionUpdateForm
from dunbud.models import Session

logger = logging.getLogger(__name__)


class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for DMs to update session details, including notes.
    """

    model = Session
    form_class = SessionUpdateForm
    template_name = "session/session_update.html"
    context_object_name = "session_obj"

    def get_object(self, queryset: Any = None) -> Session | Any:
        """
        Retrieve the Session object based on campaign_pk and session_number
        from the URL.
        """
        if queryset is None:
            queryset = self.get_queryset()

        campaign_pk = self.kwargs.get("campaign_pk")
        session_number = self.kwargs.get("session_number")

        return get_object_or_404(
            queryset,
            campaign__id=campaign_pk,
            session_number=session_number,
        )

    def test_func(self) -> bool:
        """
        Ensure only the DM can update the session.
        """
        session = self.get_object()
        user = self.request.user
        return session.campaign.dungeon_master == user

    def get_success_url(self) -> str:
        """
        Redirects back to the session detail page.
        """
        return reverse(
            "session_detail",
            kwargs={
                "campaign_pk": self.object.campaign.id,
                "session_number": self.object.session_number,
            },
        )

    def form_valid(self, form: SessionUpdateForm) -> Any:
        logger.info(
            "User %s updated session %s (Campaign: %s)",
            self.request.user.id,
            self.object.id,
            self.object.campaign.name,
        )
        return super().form_valid(form)
