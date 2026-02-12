from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from dunbud.forms import SessionCreateForm
from dunbud.models import Campaign, Session


class SessionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for creating a new session for a campaign."""

    model = Session
    form_class = SessionCreateForm
    template_name = "session/session_form.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Fetch the campaign and store it as an instance attribute."""
        self.campaign = get_object_or_404(Campaign, slug=self.kwargs["campaign_slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        """Redirect to the campaign detail page on success."""
        return reverse(
            "campaign_detail",
            kwargs={"slug": self.kwargs["campaign_slug"]},
        )

    def form_valid(self, form: SessionCreateForm) -> HttpResponse:
        """Set the campaign and proposer on the session."""
        form.instance.campaign = self.campaign
        form.instance.proposer = self.request.user
        response = super().form_valid(form)
        if self.object:
            # Default: Add DM to attendees
            self.object.attendees.add(self.campaign.dungeon_master)

            # Also add the proposer if they are not the DM to ensure they are attending
            if self.request.user != self.campaign.dungeon_master:
                self.object.attendees.add(self.request.user)
        else:
            raise TypeError("Received None object instead of Session")
        return response

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the campaign to the context."""
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.campaign
        return context

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
            self.campaign.dungeon_master == user or user in self.campaign.players.all()
        )
