from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from ..models import Session


class SessionToggleAttendanceView(LoginRequiredMixin, View):
    """View for toggling a user's attendance for a session."""

    def post(self, request, *args, **kwargs):
        """Toggle the user's attendance for the session."""
        session = get_object_or_404(Session, pk=self.kwargs["pk"])
        user = request.user

        if user in session.attendees.all():
            session.attendees.remove(user)
        else:
            session.attendees.add(user)

        return redirect("campaign_detail", pk=session.campaign.pk)
