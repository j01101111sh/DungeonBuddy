import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def log_user_creation(
    sender: type[CustomUser],
    instance: CustomUser,
    created: bool,
    **kwargs: Any,
) -> None:
    """Log a message whenever a new user is created."""
    if created:
        logger.info("User created (signal): %s", instance.username)
