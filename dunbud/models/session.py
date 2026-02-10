from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["proposed_date"]

    def __str__(self) -> str:
        return f"Session for {self.campaign.name} at {self.proposed_date}"
