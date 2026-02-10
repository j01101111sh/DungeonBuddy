# dunbud/models/session.py

from django.conf import settings
from django.db import models

from .campaign import Campaign


class Session(models.Model):
    """Represents a proposed or scheduled session for a campaign."""

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    proposer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="proposed_sessions",
    )
    proposed_date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in hours")
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="attended_sessions",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["proposed_date"]

    def __str__(self):
        return f"Session for {self.campaign.name} at {self.proposed_date}"
