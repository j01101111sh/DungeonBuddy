import logging
import uuid
from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from dunbud.models.player_character import PlayerCharacter
from dunbud.models.session import Session

logger = logging.getLogger(__name__)


class JournalEntry(models.Model):
    """
    Model representing a journal entry written by a player for their character.
    Can optionally be linked to a specific session.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("The unique identifier for the journal entry."),
    )
    character = models.ForeignKey(
        PlayerCharacter,
        on_delete=models.CASCADE,
        related_name="journal_entries",
        help_text=_("The character who wrote this entry."),
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_entries",
        help_text=_("The session this entry is about (optional)."),
    )
    title = models.CharField(
        max_length=255,
        help_text=_("The headline or title of the entry."),
    )
    content = models.TextField(
        help_text=_("The main body of the journal entry."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the entry was created."),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the entry was last updated."),
    )

    class Meta:
        verbose_name = _("Journal Entry")
        verbose_name_plural = _("Journal Entries")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.character.name})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the journal entry and logs the creation.
        """
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            logger.info(
                "New journal entry created: '%s' for character %s",
                self.title,
                self.character.name,
            )
