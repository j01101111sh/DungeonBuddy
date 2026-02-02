import logging
import uuid
from typing import Any

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .campaign import Campaign

logger = logging.getLogger(__name__)


class PlayerCharacter(models.Model):
    """
    Model representing a player character in a tabletop RPG.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("The unique identifier for the character."),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="characters",
        help_text=_("The user who owns this character."),
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="characters",
        help_text=_("The campaign this character belongs to."),
    )
    name = models.CharField(
        max_length=255,
        help_text=_("The name of the character."),
    )
    race = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("The race/ancestry of the character."),
    )
    character_class = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Class"),
        help_text=_("The class/job of the character."),
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text=_("The level of the character."),
    )
    bio = models.TextField(
        blank=True,
        help_text=_("Character biography and description."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the character was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the character was last updated."),
    )

    class Meta:
        verbose_name = _("PlayerCharacter")
        verbose_name_plural = _("PlayerCharacters")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the character instance.
        Logs the creation of a new player character.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            logger.info(
                "New character created: %s (ID: %s) by user %s",
                self.name,
                self.pk,
                self.user,
            )
