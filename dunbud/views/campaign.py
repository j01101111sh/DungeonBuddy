import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

from dunbud.forms import PartyFeedItemForm
from dunbud.models import Campaign, PartyFeedItem

logger = logging.getLogger(__name__)


class CampaignAnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to post a new announcement to the campaign feed.
    Restricted to the Dungeon Master.
    """

    def test_func(self) -> bool:
        """
        Only the Dungeon Master can post announcements.
        """
        self.campaign = get_object_or_404(Campaign, pk=self.kwargs["pk"])
        return bool(self.campaign.dungeon_master == self.request.user)

    def post(self, request: HttpRequest, pk: str) -> HttpResponse:
        """
        Handle POST request to create a new announcement.
        """
        form = PartyFeedItemForm(request.POST)

        if form.is_valid():
            feed_item = form.save(commit=False)
            feed_item.campaign = self.campaign
            feed_item.category = PartyFeedItem.Category.ANNOUNCEMENT
            feed_item.save()

            logger.info(
                "Announcement posted to campaign %s by user %s",
                self.campaign.id,
                request.user,
            )
            messages.success(request, "Announcement posted successfully.")
        else:
            messages.error(request, "Failed to post announcement.")

        return redirect("campaign_detail", pk=pk)
