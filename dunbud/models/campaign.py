import logging
import secrets
import uuid
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from dunbud.models.character import PlayerCharacter

from dunbud.models.tabletop_system import TabletopSystem

logger = logging.getLogger(__name__)


class Campaign(models.Model):
    """
    Model representing a tabletop roleplaying campaign.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("The unique identifier for the campaign."),
    )
    name = models.CharField(
        max_length=255,
        help_text=_("The name of the campaign."),
    )
    description = models.TextField(
        blank=True,
        help_text=_("A description of the campaign and its adventures."),
    )
    system = models.ForeignKey(
        TabletopSystem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="campaigns",
        help_text=_("The tabletop system used for this campaign."),
    )
    max_players = models.PositiveIntegerField(
        default=6,
        help_text=_("The maximum number of players allowed in the campaign."),
    )
    dungeon_master = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_campaigns",
        help_text=_("The Game Master/Dungeon Master of the campaign."),
    )
    players = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="joined_campaigns",
        blank=True,
        help_text=_("The players who are members of this campaign."),
    )
    vtt_link = models.URLField(
        blank=True,
        help_text=_("Link to the Virtual Tabletop (e.g., Foundry, Roll20)."),
    )
    video_link = models.URLField(
        blank=True,
        help_text=_("Link to the video conference (e.g., Zoom, Discord)."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("The date and time when the campaign was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("The date and time when the campaign was last updated."),
    )

    if TYPE_CHECKING:
        # Reverse relation for PlayerCharacter.campaign
        player_characters: models.Manager[PlayerCharacter]
        # Reverse relation for PartyFeedItem.campaign
        feed_items: models.Manager[
            Any
        ]  # Typed as Any to avoid circular dependency with Feed

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """
        Returns the string representation of the campaign (its name).
        """
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the campaign instance.
        Logs the creation of a new campaign.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            logger.info("New campaign created: %s (ID: %s)", self.name, self.pk)


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
