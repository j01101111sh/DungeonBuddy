import logging
import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class TabletopSystem(models.Model):
    """
    Model representing a tabletop roleplaying game system (e.g., D&D 5e, Pathfinder).
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("The unique identifier for the system."),
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=_("The name of the tabletop system."),
    )
    description = models.TextField(
        blank=True,
        help_text=_("A description of the system."),
    )

    class Meta:
        verbose_name = _("Tabletop System")
        verbose_name_plural = _("Tabletop Systems")
        ordering = ["name"]

    def __str__(self) -> str:
        """
        Returns the string representation of the system (its name).
        """
        return self.name


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
