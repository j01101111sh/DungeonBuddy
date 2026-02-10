from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max

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
        on_delete=models.SET_NULL,
        related_name="proposed_sessions",
        null=True,
    )
    proposed_date = models.DateTimeField()
    duration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Duration in hours",
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("168.00")),
        ],
    )
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="attended_sessions",
        blank=True,
    )
    busy_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="busy_sessions",
        blank=True,
    )
    session_number = models.PositiveIntegerField(
        default=1,
        help_text="The sequential number of the session within the campaign.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["proposed_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "session_number"],
                name="unique_session_number_per_campaign",
            ),
        ]

    def __str__(self) -> str:
        return f"Session for {self.campaign.name} at {self.proposed_date}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Override save to auto-increment session_number if creating a new session.
        """
        if self._state.adding:
            # Calculate the next session number for this campaign
            max_number = self.campaign.sessions.aggregate(
                Max("session_number"),
            )["session_number__max"]
            self.session_number = (max_number or 0) + 1

        super().save(*args, **kwargs)
