import logging

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class ChatMessage(models.Model):
    """
    Represents a single chat message posted in a session.
    """

    session = models.ForeignKey(
        "Session",
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self) -> str:
        return f"Message by {self.user} in {self.session} at {self.timestamp}"
