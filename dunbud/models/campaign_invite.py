import logging
import secrets
import uuid
from typing import Any

from django.db import models
from django.urls import reverse

logger = logging.getLogger(__name__)


class CampaignInvitation(models.Model):
    """
    Model representing a secure invitation link to join a Campaign.

    Attributes:
        id (UUID): Primary key.
        campaign (Campaign): The campaign this invite belongs to.
        token (str): The unique secure token for the link.
        created_at (datetime): When the invite was generated.
        is_active (bool): Whether the invite is currently valid.
    """

    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    token: models.CharField = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    is_active: models.BooleanField = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"Invite for {self.campaign.name} ({self.token[:8]}...)"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overridden save method to generate a secure token if one does not exist.
        """
        if not self.token:
            # Generate a url-safe secure token
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """
        Returns the absolute URL path to join this campaign.
        """
        return reverse("campaign_join", kwargs={"token": self.token})
