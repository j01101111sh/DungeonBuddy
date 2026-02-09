import logging
import uuid
from typing import TYPE_CHECKING

from django.db import models
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    pass

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
    short_name = models.CharField(
        max_length=30,
        unique=True,
        help_text=_("Shortened name of the tabletop system."),
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
