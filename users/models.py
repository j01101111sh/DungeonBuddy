import logging

from django.contrib.auth.models import AbstractUser
from django.db import models

logger = logging.getLogger(__name__)


class CustomUser(AbstractUser):
    """
    Custom user model
    Includes additional profile fields for public display.
    """

    bio = models.TextField(
        blank=True,
        help_text="A short bio about yourself.",
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Where you are from.",
    )
    website = models.URLField(
        blank=True,
        help_text="A link to your personal website or blog.",
    )
    is_test_user = models.BooleanField(
        default=False,
        help_text="Designates whether this user is a test user.",
    )

    def __str__(self) -> str:
        return self.username
