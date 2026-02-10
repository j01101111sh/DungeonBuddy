from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBase
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView

from ..forms import SessionForm
from ..models import Campaign, Session


class SessionCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new session for a campaign."""

    model = Session
    form_class = SessionForm
    template_name = "session/session_form.html"

    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> HttpResponseBase:
        """Fetch the campaign and store it as an instance attribute."""
        self.campaign = get_object_or_404(Campaign, pk=self.kwargs["campaign_pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        """Redirect to the campaign detail page on success."""
        return reverse(
            "campaign_detail",
            kwargs={"pk": self.kwargs["campaign_pk"]},
        )

    def form_valid(self, form: SessionForm) -> HttpResponse:
        """Set the campaign and proposer on the session."""
        form.instance.campaign = self.campaign
        form.instance.proposer = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the campaign to the context."""
        context = super().get_context_data(**kwargs)
        context["campaign"] = self.campaign
        return context
