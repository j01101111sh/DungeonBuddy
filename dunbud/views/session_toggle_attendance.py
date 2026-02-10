from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from ..models import Session


class SessionToggleAttendanceView(LoginRequiredMixin, View):
    """View for toggling a user's attendance for a session."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """Toggle the user's attendance for the session."""
        session = get_object_or_404(Session.objects.select_related("campaign"), pk=self.kwargs["pk"])
        user = request.user

        if user.is_authenticated:
            if user in session.attendees.all():
                session.attendees.remove(user)
            else:
                session.attendees.add(user)

        return redirect("campaign_detail", pk=session.campaign.pk)
