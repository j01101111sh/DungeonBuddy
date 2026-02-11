from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from dunbud.models import Session


class SessionToggleAttendanceView(LoginRequiredMixin, View):
    """View for toggling a user's attendance for a session."""

    def post(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """
        Toggle the user's attendance for the session.
        Moves user between 'attendees' and 'busy_users'.
        """
        session = get_object_or_404(
            Session.objects.select_related("campaign"),
            pk=self.kwargs["pk"],
        )
        user = request.user

        if user.is_authenticated:
            if user in session.attendees.all():
                session.attendees.remove(user)
                session.busy_users.add(user)
            elif user in session.busy_users.all():
                session.busy_users.remove(user)
                session.attendees.add(user)
            else:
                # If in neither list, default to attending
                session.attendees.add(user)

        return redirect("campaign_detail", pk=session.campaign.pk)
