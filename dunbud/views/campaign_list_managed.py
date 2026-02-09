import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, QuerySet
from django.views.generic import (
    ListView,
)

from dunbud.models import Campaign

logger = logging.getLogger(__name__)


class ManagedCampaignListView(LoginRequiredMixin, ListView):
    """
    View to list campaigns managed by the current user.
    """

    model = Campaign
    template_name = "campaign/managed_campaign_list.html"
    context_object_name = "campaigns"

    def get_queryset(self) -> QuerySet[Campaign]:
        """
        Returns the campaigns where the current user is the Dungeon Master.
        """
        if not self.request.user.is_authenticated:
            return Campaign.objects.none()

        return (
            Campaign.objects.filter(dungeon_master=self.request.user)
            .select_related("dungeon_master", "system")
            .annotate(player_count=Count("players"))
            .prefetch_related("feed_items")
        )
