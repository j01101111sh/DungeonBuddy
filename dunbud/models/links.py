from django.core.exceptions import ValidationError
from django.db import models, transaction

from dunbud.models.campaign import Campaign

MAX_LINKS_PER_CAMPAIGN = 20


class HelpfulLink(models.Model):
    """A helpful link for a campaign."""

    campaign = models.ForeignKey(
        "dunbud.Campaign",
        on_delete=models.CASCADE,
        related_name="helpful_links",
    )
    name = models.CharField(max_length=100)
    url = models.URLField()

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        """
        Validate that the campaign does not have more than 20 helpful links.
        """
        if self.pk is None and self.campaign:
            with transaction.atomic():
                campaign = (
                    Campaign.objects.select_for_update()
                    .filter(slug=self.campaign.slug)
                    .get()
                )
                if campaign.helpful_links.count() >= MAX_LINKS_PER_CAMPAIGN:
                    raise ValidationError(
                        "You can only add up to 20 helpful links per campaign.",
                    )
