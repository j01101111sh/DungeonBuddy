from django.core.exceptions import ValidationError
from django.db import models


class HelpfulLink(models.Model):
    """A helpful link for a campaign."""

    campaign = models.ForeignKey(
        "dunbud.Campaign",
        on_delete=models.CASCADE,
        related_name="helpful_links",
    )
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self):
        return self.name

    def clean(self):
        """
        Validate that the campaign does not have more than 20 helpful links.
        """
        if self.campaign.helpful_links.count() >= 20:
            raise ValidationError(
                "You can only add up to 20 helpful links per campaign.",
            )
