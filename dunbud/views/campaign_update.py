import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import UpdateView

from dunbud.models import Campaign

logger = logging.getLogger(__name__)


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View to edit an existing campaign.
    Restricted to the Dungeon Master.
    """

    model = Campaign
    fields = [
        "name",
        "description",
        "system",
        "max_players",
        "vtt_link",
        "video_link",
    ]
    template_name = "campaign/campaign_form.html"
    context_object_name = "campaign"

    def test_func(self) -> bool:
        """
        Only the Dungeon Master can edit the campaign.
        """
        campaign = self.get_object()
        return bool(campaign.dungeon_master == self.request.user)

    def get_success_url(self) -> str:
        return reverse("campaign_detail", kwargs={"pk": self.object.pk})
