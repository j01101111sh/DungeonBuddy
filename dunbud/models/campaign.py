import logging
import uuid
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from dunbud.models.player_character import PlayerCharacter

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
    # Added SlugField with unique=True for DB-level guarantee
    slug = models.SlugField(
        unique=True,
        max_length=255,
        blank=True,
        help_text=_("The URL-friendly identifier for the campaign."),
    )
    name = models.CharField(
        max_length=255,
        help_text=_("The name of the campaign."),
    )
    # ... [Rest of the fields: description, system, max_players, etc. remain unchanged] ...
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
        player_characters: models.Manager[PlayerCharacter]
        feed_items: models.Manager[Any]

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the campaign instance.
        Generates a unique slug if one does not exist.
        """
        is_new = self._state.adding

        # Ensure we have an ID for the slug generation
        if not self.id:
            self.id = uuid.uuid4()

        if not self.slug:
            self._generate_unique_slug()

        super().save(*args, **kwargs)

        if is_new:
            logger.info("New campaign created: %s (Slug: %s)", self.name, self.slug)

    def _generate_unique_slug(self) -> None:
        """
        Generates a unique slug by appending a slice of the UUID to the name.
        If a collision occurs (astronomically rare), it extends the slice.
        """
        base_slug = slugify(self.name, allow_unicode=True) or "campaign"
        uuid_str = str(self.id).replace("-", "")

        # Start with 8 characters (approx 4 billion combinations)
        # Loop to handle the tiny probability of collision
        for length in range(8, len(uuid_str) + 1, 4):
            candidate_slug = f"{base_slug}-{uuid_str[:length]}"

            # Check if this slug is taken by ANOTHER campaign
            # We exclude self.pk to allow saving updates to the same object
            if (
                not Campaign.objects.filter(slug=candidate_slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = candidate_slug
                return

        # Fallback: If for some reason the full UUID is taken (impossible),
        # append a random string or timestamp. (Should never reach here).
        self.slug = f"{base_slug}-{uuid.uuid4().hex[:12]}"
