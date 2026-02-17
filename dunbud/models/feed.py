import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .campaign import Campaign


class PartyFeedItem(models.Model):
    """
    Model representing an entry in the campaign's party feed.
    """

    class Category(models.TextChoices):
        MEMBERSHIP = "membership", _("Membership")
        ANNOUNCEMENT = "announcements", _("Announcements")
        DATA_UPDATE = "data_updates", _("Data Updates")
        JOURNAL = "journal", _("Journal")
        RECAP = "recap", _("Session Recap")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="feed_items",
        help_text=_("The campaign this feed item belongs to."),
    )
    message = models.TextField(
        help_text=_("The text content of the feed item. Supports Markdown."),
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.ANNOUNCEMENT,
        help_text=_("The category of this feed item."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When this feed item was created."),
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Party Feed Item")
        verbose_name_plural = _("Party Feed Items")

    def __str__(self) -> str:
        return f"{self.campaign.name}: [{self.category}] {self.message}"
